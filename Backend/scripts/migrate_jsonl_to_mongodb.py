# -*- coding: utf-8 -*-
"""
Data Migration Script: JSONL logs naar MongoDB

Migreert bestaande JSONL log bestanden naar MongoDB collections.
Gebruikt motor (async); installeer: python -m pip install -r requirements.txt
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.schemas.device import Device
from app.schemas.session import Session
from app.schemas.signal import SignalRecord
from app.schemas.technique import Technique
from app.schemas.feedback_rules import FeedbackRules
from app.schemas.parameter_set import ParameterSet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def enrich_with_dt(obj: dict) -> str:
    """Voegt 'dt' toe met format DD-MM-YYYY HH:MM:SS:MMM"""
    now = datetime.now()
    ms = int(now.microsecond / 1000)
    dt_str = now.strftime("%d-%m-%Y %H:%M:%S") + f":{ms:03d}"
    return dt_str


def parse_timestamp(ts: Any) -> Optional[int]:
    """Parse timestamp naar milliseconds"""
    if ts is None:
        return None
    
    try:
        ts_int = int(ts)
        # Convert nanoseconds to milliseconds
        if ts_int > 10_000_000_000_000:
            return ts_int // 1_000_000
        # Convert seconds to milliseconds
        if 1_000_000_000 < ts_int < 10_000_000_000:
            return ts_int * 1000
        # Already milliseconds
        if 1_000_000_000_000 < ts_int < 10_000_000_000_000:
            return ts_int // 1000
        if 1_000_000_000_000 <= ts_int <= 10_000_000_000_000:
            return ts_int
        # Assume milliseconds if in reasonable range
        if 1_000_000_000 < ts_int < 10_000_000_000_000:
            return ts_int
        return None
    except (ValueError, TypeError):
        return None


def parse_dt_from_ts(ts: int) -> str:
    """Convert timestamp (ms) to dt string format"""
    dt = datetime.fromtimestamp(ts / 1000.0)
    ms = ts % 1000
    return dt.strftime("%d-%m-%Y %H:%M:%S") + f":{ms:03d}"


class JSONLMigrator:
    """Migrate JSONL files to MongoDB"""

    def __init__(self, client: AsyncIOMotorClient, database_name: str):
        self.client = client
        self.db = client[database_name]
        self.stats = {
            "devices": 0,
            "sessions": 0,
            "signals": 0,
            "errors": 0,
            "files_processed": 0,
        }
    
    async def migrate_file(self, file_path: Path, device_id: str) -> Dict[str, int]:
        """Migrate a single JSONL file"""
        logger.info(f"Processing file: {file_path.name} (device: {device_id})")
        
        signals_batch: List[dict] = []
        current_session: Optional[Session] = None
        sessions: List[Session] = []
        last_breath_target: Optional[dict] = None
        
        file_stats = {
            "signals": 0,
            "sessions": 0,
            "errors": 0,
        }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Line {line_num}: JSON decode error: {e}")
                        file_stats["errors"] += 1
                        continue
                    
                    # Handle parameters line (skip, maar log)
                    if "parameters" in data:
                        logger.debug(f"Found parameters: {data.get('parameters', {}).get('version')}")
                        continue
                    
                    # Extract signal type
                    signal_type = data.get("signal")
                    if not signal_type:
                        continue
                    
                    # Parse timestamp
                    ts = parse_timestamp(data.get("ts"))
                    if ts is None:
                        logger.warning(f"Line {line_num}: Invalid timestamp")
                        file_stats["errors"] += 1
                        continue
                    
                    dt = parse_dt_from_ts(ts)
                    
                    # Handle BreathTarget - start/update session
                    if signal_type == "BreathTarget":
                        target_rr = data.get("TargetRR", 0)
                        technique_name = data.get("technique")
                        
                        # End current session if target_rr becomes 0
                        if target_rr == 0 and current_session:
                            current_session.end()
                            sessions.append(current_session)
                            current_session = None
                            last_breath_target = None
                        # Start new session if target_rr > 0
                        elif target_rr > 0:
                            if current_session:
                                current_session.end()
                                sessions.append(current_session)
                            
                            current_session = Session(
                                device_id=device_id,
                                technique_name=technique_name,
                                param_version=data.get("active_param_version", "v1_default"),
                                target_rr=target_rr,
                                started_at=datetime.fromtimestamp(ts / 1000.0),
                            )
                            last_breath_target = data
                    
                    # Create signal record
                    signal_record = SignalRecord(
                        device_id=device_id,
                        signal=signal_type,
                        ts=ts,
                        dt=dt,
                        session_id=current_session.session_id if current_session else None,
                        # ECG fields
                        samples=data.get("samples"),
                        # HR fields
                        bpm=data.get("bpm"),
                        # Resp RR fields
                        estRR=data.get("estRR"),
                        tijd=data.get("tijd"),
                        inhale=data.get("inhale"),
                        exhale=data.get("exhale"),
                        # Guidance fields
                        text=data.get("text"),
                        audio_text=data.get("audio_text"),
                        color=data.get("color"),
                        target=data.get("target"),
                        actual=data.get("actual"),
                        # BreathTarget fields
                        TargetRR=data.get("TargetRR"),
                        breath_cycle=data.get("breath_cycle"),
                        technique=data.get("technique"),
                        active_param_version=data.get("active_param_version"),
                    )
                    
                    signals_batch.append(signal_record.to_dict())
                    file_stats["signals"] += 1
                    
                    # Batch insert signals every 1000 records
                    if len(signals_batch) >= 1000:
                        await self._insert_signals_batch(signals_batch)
                        signals_batch = []
                
                # End last session if still active
                if current_session:
                    current_session.end()
                    sessions.append(current_session)
                
                # Insert remaining signals
                if signals_batch:
                    await self._insert_signals_batch(signals_batch)
                
                # Insert sessions
                if sessions:
                    await self._insert_sessions(sessions)
                    file_stats["sessions"] = len(sessions)
                
                logger.info(
                    f"Completed {file_path.name}: "
                    f"{file_stats['signals']} signals, "
                    f"{file_stats['sessions']} sessions, "
                    f"{file_stats['errors']} errors"
                )
                
                return file_stats
                
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            file_stats["errors"] += 1
            return file_stats
    
    async def _insert_signals_batch(self, signals: List[dict]) -> None:
        """Insert batch of signals"""
        if not signals:
            return
        try:
            result = await self.db.signals.insert_many(signals, ordered=False)
            self.stats["signals"] += len(result.inserted_ids)
            logger.debug(f"Inserted {len(result.inserted_ids)} signals")
        except Exception as e:
            logger.error(f"Error inserting signals batch: {e}")
            self.stats["errors"] += 1
    
    async def _insert_sessions(self, sessions: List[Session]) -> None:
        """Insert sessions"""
        if not sessions:
            return
        try:
            session_dicts = [s.to_dict() for s in sessions]
            result = await self.db.sessions.insert_many(session_dicts, ordered=False)
            self.stats["sessions"] += len(result.inserted_ids)
            logger.debug(f"Inserted {len(result.inserted_ids)} sessions")
        except Exception as e:
            logger.error(f"Error inserting sessions: {e}")
            self.stats["errors"] += 1
    
    async def ensure_device(self, device_id: str) -> Device:
        """Ensure device exists in database"""
        device_doc = await self.db.devices.find_one({"device_id": device_id})
        if device_doc:
            device = Device.from_dict(device_doc)
            device.update_last_seen()
            await self.db.devices.update_one(
                {"device_id": device_id},
                {"$set": {"last_seen": device.last_seen}},
            )
            return device
        device = Device(device_id=device_id)
        await self.db.devices.insert_one(device.to_dict())
        self.stats["devices"] += 1
        logger.info(f"Created new device: {device_id}")
        return device
    
    async def migrate_directory(self, logs_dir: Path) -> None:
        """Migrate all JSONL files from logs directory"""
        logger.info(f"Starting migration from: {logs_dir}")
        jsonl_files = list(logs_dir.rglob("*.jsonl"))
        if not jsonl_files:
            logger.warning(f"No JSONL files found in {logs_dir}")
            return
        logger.info(f"Found {len(jsonl_files)} JSONL files")
        for file_path in jsonl_files:
            device_id = file_path.parent.name if file_path.parent.name != "logs" else "UNKNOWN"
            await self.ensure_device(device_id)
            await self.migrate_file(file_path, device_id)
            self.stats["files_processed"] += 1
        
        logger.info("=" * 60)
        logger.info("Migration Summary:")
        logger.info(f"  Files processed: {self.stats['files_processed']}")
        logger.info(f"  Devices created: {self.stats['devices']}")
        logger.info(f"  Sessions created: {self.stats['sessions']}")
        logger.info(f"  Signals inserted: {self.stats['signals']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info("=" * 60)


async def migrate_techniques(client: AsyncIOMotorClient, database_name: str, techniques_file: Path) -> None:
    """Migrate techniques.json to MongoDB"""
    logger.info(f"Migrating techniques from: {techniques_file}")
    if not techniques_file.exists():
        logger.warning(f"Techniques file not found: {techniques_file}")
        return
    db = client[database_name]
    try:
        with open(techniques_file, "r", encoding="utf-8") as f:
            techniques_data = json.load(f)
        techniques = []
        for name, data in techniques_data.items():
            technique = Technique(
                name=name,
                description=data.get("description", ""),
                param_version=data.get("param_version", "Default"),
                show_in_app=data.get("show_in_app", False),
                protocol=data.get("protocol", []),
                is_active=True,  # /techniques/public filtert op show_in_app + is_active
            )
            techniques.append(technique.to_dict())
        if techniques:
            result = await db.techniques.insert_many(techniques, ordered=False)
            logger.info(f"Inserted {len(result.inserted_ids)} techniques")
    except Exception as e:
        logger.error(f"Error migrating techniques: {e}", exc_info=True)


async def migrate_feedback_rules(client: AsyncIOMotorClient, database_name: str, rules_file: Path) -> None:
    """Migrate feedback_rules.json to MongoDB"""
    logger.info(f"Migrating feedback rules from: {rules_file}")
    if not rules_file.exists():
        logger.warning(f"Feedback rules file not found: {rules_file}")
        return
    db = client[database_name]
    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
        feedback_rules = FeedbackRules(rules=rules_data)
        existing = await db.feedback_rules.find_one({"_id": feedback_rules._id})
        if existing:
            logger.info("Feedback rules already exist, skipping")
        else:
            await db.feedback_rules.insert_one(feedback_rules.to_dict())
            logger.info("Inserted feedback rules")
    except Exception as e:
        logger.error(f"Error migrating feedback rules: {e}", exc_info=True)


async def migrate_parameter_sets(client: AsyncIOMotorClient, database_name: str, param_file: Path) -> None:
    """Migrate resp_rr_param_sets.json to MongoDB"""
    logger.info(f"Migrating parameter sets from: {param_file}")
    
    if not param_file.exists():
        logger.warning(f"Parameter sets file not found: {param_file}")
        return
    
    db = client[database_name]
    
    try:
        with open(param_file, "r", encoding="utf-8") as f:
            param_data = json.load(f)
        
        param_sets = []
        for item in param_data:
            version = item.get("version")
            if not version:
                continue
            
            param_set = ParameterSet(
                version=version,
                BP_LOW_HZ=item["BP_LOW_HZ"],
                BP_HIGH_HZ=item["BP_HIGH_HZ"],
                MWA_QRS_SEC=item["MWA_QRS_SEC"],
                MWA_BEAT_SEC=item["MWA_BEAT_SEC"],
                MIN_SEG_SEC=item["MIN_SEG_SEC"],
                MIN_RR_SEC=item["MIN_RR_SEC"],
                QRS_HALF_SEC=item["QRS_HALF_SEC"],
                HEARTBEAT_WINDOW=item["HEARTBEAT_WINDOW"],
                FFT_LENGTH=item["FFT_LENGTH"],
                FREQ_RANGE_CB=item["FREQ_RANGE_CB"],
                SMOOTH_WIN=item["SMOOTH_WIN"],
                BPM_MIN=item["BPM_MIN"],
                BPM_MAX=item["BPM_MAX"],
                HARMONIC_RATIO=item["HARMONIC_RATIO"],
                BUFFER_SIZE=item["BUFFER_SIZE"],
                is_default=(version == "Default"),
            )
            param_sets.append(param_set.to_dict())
        
        if param_sets:
            result = await db.parameter_sets.insert_many(param_sets, ordered=False)
            logger.info(f"Inserted {len(result.inserted_ids)} parameter sets")
    except Exception as e:
        logger.error(f"Error migrating parameter sets: {e}", exc_info=True)


async def main() -> None:
    """Main migration function"""
    # Paths
    project_root = Path(__file__).parent.parent.parent
    old_server_dir = project_root / "SerenaWebApp" / "pythonbleakgui_server"
    logs_dir = old_server_dir / "logs"
    techniques_file = old_server_dir / "server" / "techniques.json"
    rules_file = old_server_dir / "server" / "feedback_rules.json"
    param_file = old_server_dir / "resp_rr_param_sets.json"
    
    logger.info(f"Connecting to MongoDB: {settings.mongodb_uri}")
    client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)

    try:
        await client.admin.command("ping")
        logger.info("Connected to MongoDB")

        migrator = JSONLMigrator(client, settings.mongo_database)

        if logs_dir.exists():
            await migrator.migrate_directory(logs_dir)
        else:
            logger.warning(f"Logs directory not found: {logs_dir}")

        if techniques_file.exists():
            await migrate_techniques(client, settings.mongo_database, techniques_file)

        if rules_file.exists():
            await migrate_feedback_rules(client, settings.mongo_database, rules_file)

        if param_file.exists():
            await migrate_parameter_sets(client, settings.mongo_database, param_file)

        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
