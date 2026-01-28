/**
 * Offline Queue Service
 * Stores data locally when offline and syncs when online
 */
import { storageService } from './storage';
import { apiClient } from './api/client';
import type { RecordIngest } from './api/types';

const QUEUE_KEY = '@serena:offline_queue';
const MAX_QUEUE_SIZE = 1000;

interface QueuedItem {
  id: string;
  timestamp: number;
  data: RecordIngest | RecordIngest[];
  retries: number;
}

class OfflineQueue {
  private syncing = false;

  /**
   * Add item(s) to offline queue
   */
  async enqueue(data: RecordIngest | RecordIngest[]): Promise<void> {
    try {
      const queue = await this.getQueue();
      const item: QueuedItem = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: Date.now(),
        data: Array.isArray(data) ? data : [data],
        retries: 0,
      };

      queue.push(item);

      // Limit queue size
      if (queue.length > MAX_QUEUE_SIZE) {
        queue.shift(); // Remove oldest items
      }

      await storageService.set(QUEUE_KEY, queue);
    } catch (error) {
      console.error('[OfflineQueue] Failed to enqueue:', error);
      throw error;
    }
  }

  /**
   * Get current queue
   */
  async getQueue(): Promise<QueuedItem[]> {
    try {
      const queue = await storageService.get<QueuedItem[]>(QUEUE_KEY, []);
      return queue || [];
    } catch (error) {
      console.error('[OfflineQueue] Failed to get queue:', error);
      return [];
    }
  }

  /**
   * Get queue size
   */
  async getQueueSize(): Promise<number> {
    const queue = await this.getQueue();
    return queue.length;
  }

  /**
   * Sync queue to server
   */
  async sync(isOnline: boolean): Promise<{ synced: number; failed: number }> {
    if (!isOnline || this.syncing) {
      return { synced: 0, failed: 0 };
    }

    this.syncing = true;
    const queue = await this.getQueue();
    let synced = 0;
    let failed = 0;

    try {
      // Process queue in batches
      const batchSize = 50;
      for (let i = 0; i < queue.length; i += batchSize) {
        const batch = queue.slice(i, i + batchSize);
        const allRecords: RecordIngest[] = [];

        // Flatten batch
        for (const item of batch) {
          if (Array.isArray(item.data)) {
            allRecords.push(...item.data);
          } else {
            allRecords.push(item.data);
          }
        }

        try {
          // Try to sync batch
          await apiClient.ingestRecords(allRecords);
          synced += batch.length;

          // Remove synced items from queue
          const syncedIds = new Set(batch.map((item) => item.id));
          const remainingQueue = queue.filter((item) => !syncedIds.has(item.id));
          await storageService.set(QUEUE_KEY, remainingQueue);
        } catch (error) {
          console.error('[OfflineQueue] Failed to sync batch:', error);
          failed += batch.length;

          // Increment retry count for failed items
          for (const item of batch) {
            item.retries += 1;
          }

          // Remove items that have exceeded max retries (10)
          const filteredQueue = queue.filter((item) => item.retries < 10);
          await storageService.set(QUEUE_KEY, filteredQueue);
        }
      }
    } catch (error) {
      console.error('[OfflineQueue] Sync error:', error);
    } finally {
      this.syncing = false;
    }

    return { synced, failed };
  }

  /**
   * Clear queue
   */
  async clear(): Promise<void> {
    try {
      await storageService.remove(QUEUE_KEY);
    } catch (error) {
      console.error('[OfflineQueue] Failed to clear queue:', error);
      throw error;
    }
  }

  /**
   * Remove specific item from queue
   */
  async removeItem(itemId: string): Promise<void> {
    try {
      const queue = await this.getQueue();
      const filtered = queue.filter((item) => item.id !== itemId);
      await storageService.set(QUEUE_KEY, filtered);
    } catch (error) {
      console.error('[OfflineQueue] Failed to remove item:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const offlineQueue = new OfflineQueue();
export default offlineQueue;
