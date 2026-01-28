# -*- coding: utf-8 -*-
"""List all API routes"""
from app.main import app

print("=" * 70)
print("Serena Backend API Routes")
print("=" * 70)

routes = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        methods = ', '.join(sorted(route.methods))
        routes.append((methods, route.path))

routes.sort(key=lambda x: x[1])

print(f"\nTotal: {len(routes)} routes\n")
for methods, path in routes:
    print(f"  {methods:20} {path}")

print("\n" + "=" * 70)
