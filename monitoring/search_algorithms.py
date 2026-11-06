"""A* and Greedy Best-First search over CloudPilot's demo VM-size graph.

The search graph is intentionally small and pedagogical: small <-> medium <-> large.
The goal is the least-size VM profile satisfying estimated CPU and RAM demand.
"""
import heapq

VM_CAPACITY = {
    'small': {'vcpu': 2, 'ram_gb': 4},
    'medium': {'vcpu': 4, 'ram_gb': 8},
    'large': {'vcpu': 8, 'ram_gb': 16},
}
VM_NEIGHBORS = {
    'small': ['medium'],
    'medium': ['small', 'large'],
    'large': ['medium'],
}
VM_ORDER = {'small': 0, 'medium': 1, 'large': 2}


def _satisfies(vm_type, required_vcpu, required_ram):
    capacity = VM_CAPACITY[vm_type]
    return capacity['vcpu'] >= required_vcpu and capacity['ram_gb'] >= required_ram


def _reconstruct(parent, goal):
    path = [goal]
    while path[-1] in parent:
        path.append(parent[path[-1]])
    return list(reversed(path))


def _goal_profiles(required_vcpu, required_ram):
    return [name for name in VM_CAPACITY if _satisfies(name, required_vcpu, required_ram)]


def _heuristic(vm_type, goal_profiles):
    """Exact graph distance to the nearest goal; admissible for A* with unit edges."""
    if not goal_profiles:
        return 0
    return min(abs(VM_ORDER[vm_type] - VM_ORDER[goal]) for goal in goal_profiles)


def astar_vm_search(required_vcpu, required_ram):
    """Find the least-cost feasible VM profile using A* (start from smallest size)."""
    start = 'small'
    goals = _goal_profiles(required_vcpu, required_ram)
    if not goals:
        return {'target': 'large', 'path': ['small', 'medium', 'large'], 'feasible': False}
    frontier = [(_heuristic(start, goals), 0, start)]
    parent, cost_so_far = {}, {start: 0}
    while frontier:
        _, cost, current = heapq.heappop(frontier)
        if current in goals:
            return {'target': current, 'path': _reconstruct(parent, current), 'feasible': True}
        for neighbor in VM_NEIGHBORS[current]:
            new_cost = cost + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                parent[neighbor] = current
                priority = new_cost + _heuristic(neighbor, goals)
                heapq.heappush(frontier, (priority, new_cost, neighbor))
    return {'target': 'large', 'path': ['small', 'medium', 'large'], 'feasible': False}


def best_first_vm_search(required_vcpu, required_ram):
    """Greedy Best-First baseline using only distance to the nearest feasible profile."""
    start = 'small'
    goals = _goal_profiles(required_vcpu, required_ram)
    if not goals:
        return {'target': 'large', 'path': ['small', 'medium', 'large'], 'feasible': False}
    frontier = [(_heuristic(start, goals), start)]
    visited, parent = set(), {}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current in visited:
            continue
        visited.add(current)
        if current in goals:
            return {'target': current, 'path': _reconstruct(parent, current), 'feasible': True}
        for neighbor in VM_NEIGHBORS[current]:
            if neighbor not in visited:
                parent.setdefault(neighbor, current)
                heapq.heappush(frontier, (_heuristic(neighbor, goals), neighbor))
    return {'target': 'large', 'path': ['small', 'medium', 'large'], 'feasible': False}


def path_between_vm_sizes(start, target):
    """Return the shortest upgrade/downgrade path in the VM-size graph."""
    if start not in VM_CAPACITY or target not in VM_CAPACITY:
        raise ValueError('Unknown VM size.')
    if start == target:
        return [start]
    parent, queue = {}, [start]
    visited = {start}
    for current in queue:
        for neighbor in VM_NEIGHBORS[current]:
            if neighbor in visited:
                continue
            visited.add(neighbor)
            parent[neighbor] = current
            if neighbor == target:
                return _reconstruct(parent, target)
            queue.append(neighbor)
    return [start]
