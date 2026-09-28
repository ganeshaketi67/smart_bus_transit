"""Breadth-First Search (BFS) graph utilities for transit networks."""

from collections import deque


def build_graph_from_db(network_data: list[dict]) -> tuple[dict[str, list[dict]], dict[tuple[str, str], list[str]]]:
    """
    Build adjacency list and route mapping from DB network rows.
    Returns:
      - graph: dict where stop_name -> list of {neighbor, route_code, distance}
      - route_map: dict where (stop_a, stop_b) -> list of route_codes serving this leg
    """
    graph: dict[str, list[dict]] = {}
    route_map: dict[tuple[str, str], list[str]] = {}

    # Group stops by route_id
    routes_dict: dict[int, list[dict]] = {}
    for row in network_data:
        r_id = row["route_id"]
        if r_id not in routes_dict:
            routes_dict[r_id] = []
        routes_dict[r_id].append(row)

    for r_id, stops in routes_dict.items():
        sorted_stops = sorted(stops, key=lambda s: s["stop_order"])
        route_code = sorted_stops[0]["route_name"]

        for i in range(len(sorted_stops) - 1):
            curr_stop = sorted_stops[i]["stop_name"]
            next_stop = sorted_stops[i + 1]["stop_name"]

            # Initialize lists
            if curr_stop not in graph:
                graph[curr_stop] = []
            if next_stop not in graph:
                graph[next_stop] = []

            # Add directed/undirected edges
            if not any(edge["neighbor"] == next_stop and edge["route"] == route_code for edge in graph[curr_stop]):
                graph[curr_stop].append({"neighbor": next_stop, "route": route_code})
            if not any(edge["neighbor"] == curr_stop and edge["route"] == route_code for edge in graph[next_stop]):
                graph[next_stop].append({"neighbor": curr_stop, "route": route_code})

            edge_key1 = (curr_stop, next_stop)
            edge_key2 = (next_stop, curr_stop)
            if edge_key1 not in route_map:
                route_map[edge_key1] = []
            if route_code not in route_map[edge_key1]:
                route_map[edge_key1].append(route_code)

            if edge_key2 not in route_map:
                route_map[edge_key2] = []
            if route_code not in route_map[edge_key2]:
                route_map[edge_key2].append(route_code)

    return graph, route_map


def shortest_route(graph_or_adj: dict, start: str, destination: str) -> list[str]:
    """Return the shortest route (list of stops) from start to destination, or empty list."""
    if start == destination:
        return [start]

    # Handle standard adjacency list: dict[str, list[str]] or dict[str, list[dict]]
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        stop, path = queue.popleft()
        if stop == destination:
            return path

        neighbors = graph_or_adj.get(stop, [])
        for item in neighbors:
            neighbor = item["neighbor"] if isinstance(item, dict) else item
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []


def find_detailed_path(graph: dict[str, list[dict]], route_map: dict[tuple[str, str], list[str]], start: str, destination: str) -> dict:
    """
    Perform BFS to find the minimum-hop path and build step-by-step transfer itinerary.
    """
    path = shortest_route(graph, start, destination)
    if not path or len(path) < 2:
        return {
            "found": len(path) > 0,
            "path": path,
            "segments": [],
            "transfers": 0,
            "total_hops": max(0, len(path) - 1)
        }

    segments = []
    current_route = None
    segment_start = path[0]

    for i in range(len(path) - 1):
        leg = (path[i], path[i + 1])
        available_routes = route_map.get(leg, [])
        
        # Pick current route if it continues, otherwise switch
        if current_route in available_routes:
            chosen_route = current_route
        else:
            chosen_route = available_routes[0] if available_routes else "Transit Route"
            if current_route is not None:
                # We transferred
                segments.append({
                    "from_stop": segment_start,
                    "to_stop": path[i],
                    "route": current_route,
                })
                segment_start = path[i]

        current_route = chosen_route

    # Add final segment
    segments.append({
        "from_stop": segment_start,
        "to_stop": path[-1],
        "route": current_route,
    })

    return {
        "found": True,
        "path": path,
        "segments": segments,
        "transfers": max(0, len(segments) - 1),
        "total_hops": len(path) - 1
    }