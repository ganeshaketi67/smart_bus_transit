"""
Smart Transit AI Assistant Module
Integrates real-time database context retrieval with Google Gemini Generative AI.
Provides intelligent transit predictions, schedule queries, route recommendations, fare calculations, and operator analytics.
"""

import os
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent
ENV_FILE = PROJECT_DIR / ".env"
load_dotenv(ENV_FILE)

from database import (
    get_routes,
    get_stops,
    get_trips,
    get_ridership,
    get_route_stops,
    get_overcrowding_alerts,
    get_network_graph_data,
    get_route_ridership_analytics,
    calculate_ticket_fare,
)


def get_stored_api_key() -> str:
    """Retrieve Gemini API key from environment or .env file."""
    return os.environ.get("GEMINI_API_KEY", "").strip()


def save_api_key(api_key: str) -> bool:
    """Save API key to .env file for persistence."""
    try:
        api_key = api_key.strip()
        os.environ["GEMINI_API_KEY"] = api_key
        
        # Read existing .env lines
        lines = []
        if ENV_FILE.exists():
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if not l.startswith("GEMINI_API_KEY=")]
        
        lines.append(f"GEMINI_API_KEY={api_key}\n")
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"Error saving API key: {e}")
        return False


def build_live_transit_context() -> str:
    """
    Dynamically extract all live data from the database into structured text
    for real-time LLM grounding and prediction.
    """
    routes = [dict(r) for r in get_routes()]
    stops = [dict(s) for s in get_stops()]
    trips = [dict(t) for t in get_trips()]
    ridership = [dict(rd) for rd in get_ridership()]
    alerts = [dict(al) for al in get_overcrowding_alerts()]
    analytics = [dict(an) for an in get_route_ridership_analytics()]

    context_lines = []
    context_lines.append(f"=== LIVE SMART TRANSIT DATABASE SNAPSHOT ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===")
    
    # 1. ROUTES & STOP SEQUENCES & FARE PRICING
    context_lines.append("\n[ACTIVE ROUTES, STOPS, DISTANCES & TICKET FARES]:")
    if not routes:
        context_lines.append("No active routes registered in the system.")
    else:
        for r in routes:
            r_id = r.get("id")
            r_name = r.get("route_name", f"Route#{r_id}")
            r_src = r.get("source", "N/A")
            r_dst = r.get("destination", "N/A")
            r_dist = r.get("distance", 0)
            base_fare = r.get("base_fare", 10.0)
            fare_per_km = r.get("fare_per_km", 2.5)
            min_fare = r.get("min_fare", 10.0)
            
            # Fetch stop sequence
            raw_stops = get_route_stops(r_id)
            seq_stops = [dict(s) for s in raw_stops] if raw_stops else []
            if seq_stops:
                stop_path = " -> ".join([f"{s.get('stop_name', '')} ({s.get('distance_from_origin', 0.0)}km)" for s in seq_stops if s.get("stop_name")])
            else:
                stop_path = f"{r_src} (0km) -> {r_dst} ({r_dist}km)"
            
            # Fetch trips for this route
            r_trips = [t for t in trips if t.get("route_id") == r_id]
            trip_times = [f"{t.get('departure', 'N/A')} (Bus: {t.get('bus_number', 'N/A')})" for t in r_trips]
            trip_str = ", ".join(trip_times) if trip_times else "No active trips scheduled"
            
            # Full journey fare
            total_fare_calc = max(min_fare, round(base_fare + (float(r_dist or 0) * fare_per_km)))
            
            context_lines.append(
                f"- Route ID {r_id} (Route {r_name}): {r_src} to {r_dst} ({r_dist} km)\n"
                f"  Ticket Fare Pricing: Base Fare = ₹{base_fare}, Rate = ₹{fare_per_km}/km (Min ₹{min_fare}). Full End-to-End Fare = ₹{total_fare_calc}\n"
                f"  Formula: Ticket Cost = Base Fare + (Distance between stops × Rate/km)\n"
                f"  Stops & Cumulative Distances: {stop_path}\n"
                f"  Scheduled Departures: {trip_str}"
            )

    # 2. ALL REGISTERED STOPS
    context_lines.append("\n[ALL REGISTERED BUS STOPS]:")
    if stops:
        stop_names = [s.get("stop_name", "") for s in stops if s.get("stop_name")]
        context_lines.append(", ".join(stop_names))
    else:
        context_lines.append("No stops registered.")

    # 3. SCHEDULED TRIPS OVERVIEW
    context_lines.append(f"\n[SCHEDULED TRIPS] (Total: {len(trips)} trips):")
    for t in trips[:25]:  # Up to 25 trips
        r_info = next((r for r in routes if r.get("id") == t.get("route_id")), None)
        r_name = r_info.get("route_name") if r_info else f"Route#{t.get('route_id')}"
        context_lines.append(
            f"- Bus {t.get('bus_number', 'N/A')} on Route {r_name}: Departure {t.get('departure', 'N/A')}, Arrival {t.get('arrival', 'N/A')}, Date: {t.get('trip_date', 'Daily')}"
        )

    # 4. RIDERSHIP, REVENUE & PASSENGER DEMAND
    context_lines.append("\n[ROUTE RIDERSHIP, REVENUE & PASSENGER VOLUME RANKINGS]:")
    if analytics:
        sorted_by_passengers = sorted(analytics, key=lambda x: x.get("total_passengers", 0), reverse=True)
        for rank, a in enumerate(sorted_by_passengers, start=1):
            r_name = a.get("route_name", "N/A")
            r_src = a.get("source", "Origin")
            r_dst = a.get("destination", "Destination")
            tot_p = a.get("total_passengers", 0)
            avg_p = round(float(a.get("avg_passengers_per_record") or a.get("avg_passengers") or 0), 1)
            b_fare = float(a.get("base_fare") or 10.0)
            f_rate = float(a.get("fare_per_km") or 2.5)
            dist_val = float(a.get("distance") or 10.0)
            avg_route_fare = max(10.0, round(b_fare + (dist_val * 0.7 * f_rate)))
            rev_est = tot_p * avg_route_fare
            context_lines.append(
                f"- Rank #{rank} (Route {r_name}: {r_src} ➔ {r_dst}): "
                f"Total Passengers = {tot_p:,}, Avg Passengers/Trip = {avg_p}, "
                f"Estimated Total Revenue = ₹{rev_est:,.0f} (Avg fare ₹{avg_route_fare:.0f}/ticket based on distance)"
            )
    else:
        context_lines.append("No ridership analytics recorded yet.")

    # 5. OVERCROWDING ALERTS
    context_lines.append("\n[LIVE OVERCROWDING ALERTS]:")
    if alerts:
        for al in alerts:
            context_lines.append(
                f"- Alert ID {al.get('id')}: Bus {al.get('bus_number')} on Route {al.get('route_name', 'N/A')} reported at stop '{al.get('stop_name')}' on {al.get('report_date')} {al.get('report_time')}. Status: {al.get('status')}. Notes: {al.get('passenger_notes', 'N/A')}"
            )
    else:
        context_lines.append("No active overcrowding alerts.")

    return "\n".join(context_lines)


def get_available_gemini_models():
    """List recommended Gemini models."""
    return [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro",
        "gemini-2.5-flash-lite"
    ]


def answer_with_gemini(
    query: str,
    api_key: str,
    model_name: str = "gemini-3.8-flash",
    chat_history: list = None,
    user_role: str = "passenger"
) -> dict:
    """
    Send prompt grounded in live transit context to Google Gemini.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return {
            "success": False,
            "message": "The `google-generativeai` package is not installed. Please install it using `pip install google-generativeai`."
        }

    if not api_key:
        return {
            "success": False,
            "message": "Gemini API key is not configured. Please set your GEMINI_API_KEY in .env or enter it in settings."
        }

    try:
        genai.configure(api_key=api_key)
        
        live_context = build_live_transit_context()
        
        system_instruction = f"""
You are the official Smart City Transit AI Assistant. You are friendly, concise, and helpful.
You provide accurate transit advice, bus schedules, ticket fare estimates based on distance between stops, crowd predictions, and route navigation to passengers and transit operators.

CRITICAL INSTRUCTIONS:
1. ALWAYS ground your answers in the provided LIVE SMART TRANSIT DATABASE SNAPSHOT below.
2. For ticket pricing questions: Use the exact formula (Base Fare + Distance between stops × Fare/km) or specific route pricing provided in the snapshot. Explain the distance and calculation clearly.
3. Be direct, clear, and easy to read using markdown bullet points and emojis.
4. If a user asks about timings, provide specific bus numbers and departure times from the snapshot.
5. If you do not find a direct bus for a specific stop pair, suggest looking at connecting routes or using the Route Finder.

{live_context}
"""
        
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction
        )
        
        history_prompts = []
        if chat_history:
            for msg in chat_history[-6:]:  # Last 6 exchanges
                role = "user" if msg["role"] == "user" else "model"
                history_prompts.append({"role": role, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history_prompts)
        response = chat.send_message(query)
        
        return {
            "success": True,
            "response": response.text,
            "model": model_name
        }

    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg and model_name != "gemini-3.8-flash":
            return answer_with_gemini(query, api_key, model_name="gemini-3.8-flash", chat_history=chat_history, user_role=user_role)
        return {
            "success": False,
            "message": f"Gemini API Error: {error_msg}"
        }


def dynamic_database_search_response(query: str) -> str:
    """
    Fallback intelligent response generator based directly on SQLite records
    when an external LLM API key is not configured.
    """
    routes = [dict(r) for r in get_routes()]
    stops = [dict(s) for s in get_stops()]
    trips = [dict(t) for t in get_trips()]
    alerts = [dict(al) for al in get_overcrowding_alerts()]

    q_lower = query.lower()

    if not routes and not stops:
        return (
            "⚠️ **The transit database is currently empty.**\n\n"
            "Please click **'🌱 Populate Sample City Data'** in the sidebar or add new routes in the Operator Backend."
        )

    # 1. Search for matching stops
    matched_stops = []
    for s in stops:
        s_name = s.get("stop_name", "")
        if s_name and s_name.lower() in q_lower:
            matched_stops.append(s_name)

    # Search for matching route names
    matched_routes = []
    for r in routes:
        r_name = str(r.get("route_name", ""))
        r_src = str(r.get("source", ""))
        r_dst = str(r.get("destination", ""))
        if (r_name.lower() in q_lower or 
            r_src.lower() in q_lower or 
            r_dst.lower() in q_lower):
            matched_routes.append(r)

    response_parts = []
    
    # Fare / Ticket cost search
    is_fare_query = any(w in q_lower for w in ["fare", "ticket", "cost", "price", "how much", "rate", "rupee", "₹"])

    if len(matched_stops) >= 2:
        origin, dest = matched_stops[0], matched_stops[1]
        response_parts.append(f"🔍 **Live Transit Search: {origin} ➔ {dest}**\n")
        
        direct_found = False
        for r in routes:
            raw_seq = get_route_stops(r["id"])
            r_seq = [st["stop_name"] for st in raw_seq] if raw_seq else [r.get("source", ""), r.get("destination", "")]
            r_seq_lower = [x.lower() for x in r_seq]
            if origin.lower() in r_seq_lower and dest.lower() in r_seq_lower:
                i_org = r_seq_lower.index(origin.lower())
                i_dst = r_seq_lower.index(dest.lower())
                if i_org < i_dst:
                    direct_found = True
                    r_trips = [t for t in trips if t.get("route_id") == r["id"]]
                    deps = ", ".join([f"`{t.get('departure', 'N/A')}` ({t.get('bus_number', 'N/A')})" for t in r_trips]) if r_trips else "Regular Service Scheduled"
                    fare_info = calculate_ticket_fare(r["id"], origin, dest)
                    
                    response_parts.append(f"• **Route {r.get('route_name')} ({r.get('source')} ➔ {r.get('destination')})**")
                    response_parts.append(f"  - **Stops:** {' ➔ '.join(r_seq[i_org:i_dst+1])}")
                    response_parts.append(f"  - **Distance:** {fare_info['distance']} km")
                    response_parts.append(f"  - **🎟️ Ticket Fare:** **₹{fare_info['fare']}** (Base ₹{fare_info['base_fare']} + ₹{fare_info['fare_per_km']}/km)")
                    response_parts.append(f"  - **Departure Times:** {deps}")
                    response_parts.append(f"  - **Estimated Journey Time:** ~{max(12, int(fare_info['distance'] * 3))} mins\n")

        if not direct_found:
            response_parts.append("No single direct route covers both stops directly. Check **'🗺️ Route Finder'** for transfer connections.")

    elif matched_stops:
        stop = matched_stops[0]
        response_parts.append(f"📍 **Buses serving stop '{stop}':**\n")
        found = False
        for r in routes:
            raw_seq = get_route_stops(r["id"])
            r_seq = [st["stop_name"] for st in raw_seq] if raw_seq else [r.get("source", ""), r.get("destination", "")]
            if any(stop.lower() in x.lower() for x in r_seq):
                found = True
                r_trips = [t for t in trips if t.get("route_id") == r["id"]]
                deps = ", ".join([f"`{t.get('departure', 'N/A')}` ({t.get('bus_number', 'N/A')})" for t in r_trips[:3]]) if r_trips else "Scheduled"
                response_parts.append(f"• **Route {r.get('route_name')}**: {r.get('source')} ➔ {r.get('destination')} (Fare Rate: ₹{r.get('base_fare', 10)}+₹{r.get('fare_per_km', 2.5)}/km | Next: {deps})")
        if not found:
            response_parts.append("No active routes currently stop here.")

    elif matched_routes:
        for r in matched_routes[:2]:
            raw_seq = get_route_stops(r["id"])
            r_seq = [st["stop_name"] for st in raw_seq] if raw_seq else [r.get("source", ""), r.get("destination", "")]
            r_trips = [t for t in trips if t.get("route_id") == r["id"]]
            deps = ", ".join([f"`{t.get('departure', 'N/A')}` ({t.get('bus_number', 'N/A')})" for t in r_trips]) if r_trips else "No active trips"
            total_fare = max(float(r.get("min_fare", 10)), round(float(r.get("base_fare", 10)) + float(r.get("distance", 10)) * float(r.get("fare_per_km", 2.5))))
            response_parts.append(f"🚌 **Route {r.get('route_name')} Details:**")
            response_parts.append(f"• **Endpoints:** {r.get('source')} ➔ {r.get('destination')} ({r.get('distance', 0)} km)")
            response_parts.append(f"• **🎟️ Ticket Fare Structure:** Base Fare = ₹{r.get('base_fare', 10)}, Rate = ₹{r.get('fare_per_km', 2.5)}/km (End-to-End: ₹{total_fare})")
            response_parts.append(f"• **Stop Sequence:** {' ➔ '.join(r_seq)}")
            response_parts.append(f"• **Scheduled Trips:** {deps}\n")

    else:
        # General overview
        response_parts.append("🤖 **Live Transit & Fare Information:**")
        response_parts.append(f"Currently tracking **{len(routes)} routes**, **{len(stops)} stops**, and **{len(trips)} scheduled trips**.")
        response_parts.append("\n**Active Routes & Base Fare Rates:**")
        for r in routes[:4]:
            response_parts.append(f"• **Route {r.get('route_name')}**: {r.get('source')} ➔ {r.get('destination')} ({r.get('distance', 0)}km • Base ₹{r.get('base_fare', 10)} + ₹{r.get('fare_per_km', 2.5)}/km)")

    # Prediction insights
    if "predict" in q_lower or "crowd" in q_lower or "busy" in q_lower or "peak" in q_lower:
        response_parts.append("\n📈 **Predictive AI Insights:**")
        response_parts.append("• **Peak Demand Hours:** Typically 08:00 - 10:30 AM and 05:00 - 08:00 PM.")
        response_parts.append("• **Crowd Prediction:** Moderate to High load expected during morning/evening commute.")
        if alerts:
            response_parts.append(f"• **Recent Overcrowding Reports:** {len(alerts)} alerts logged today.")

    return "\n".join(response_parts)
