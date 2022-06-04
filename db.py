# Esto esta bastante mal Flask maneja workers
# que `pueden` acceder concurrentemente a este dict.

# TODO: usar db real

KNOWN_DEVICES_ID = ['esp32', 'riscv', 'argon','test']

# { <device_id>: { <task_name>: <task_value>, ... }}

db = {}

# Tareas pendientes a ser ejecutadas
# por c/ dispositivo.

pending_tasks = {d: set() for d in KNOWN_DEVICES_ID}
