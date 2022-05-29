# Esto esta bastante mal Flask maneja workers
# que `pueden` acceder concurrentemente a este dict.

# TODO: usar db real

# -- Formato de registros
# -- Asumimos que si no tiene valor es porque todavia no fue ejecutada.
#
# { <device_id>: { <task_name>: <task_value>, ... }}

db = {}
