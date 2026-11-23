from ..schemas import StoryboardRequest


BEATS = [
    ("The opening frame", "Lead with the most visually striking establishing shot.", "0:00"),
    ("The journey", "Build anticipation with movement, roads, arrivals and changing scenery.", "0:06"),
    ("The experience", "Show the signature activity and the people who made the trip memorable.", "0:14"),
    ("The little moments", "Slow down for food, details, candid reactions and quiet discoveries.", "0:25"),
    ("The finale", "End on a wide view or warm closing moment, then let the image breathe.", "0:36"),
]


def build_storyboard(request: StoryboardRequest) -> dict:
    duration = request.target_duration_seconds
    weights = [0.14, 0.20, 0.28, 0.20, 0.18]
    cursor = 0
    scenes = []
    for index, (title, direction, _) in enumerate(BEATS):
        seconds = max(3, round(duration * weights[index]))
        start = cursor
        cursor += seconds
        scenes.append({
            "id": f"scene-{index + 1}",
            "title": title,
            "direction": direction,
            "start_seconds": start,
            "duration_seconds": seconds,
            "suggested_shot": ["wide establishing", "movement", "action", "close-up / candid", "hero wide"][index],
        })

    return {
        "title": f"{request.destination.strip() or 'Your trip'} — the story",
        "destination": request.destination,
        "mood": request.mood,
        "aspect_ratio": request.aspect_ratio,
        "target_duration_seconds": duration,
        "trip_summary": request.trip_description.strip() or "A collection of moments from your journey.",
        "scenes": scenes,
        "note": "Starter storyboard generated locally from a reusable travel-film structure. It does not claim to have analysed your footage yet; assign clips to scenes and refine the direction before rendering.",
    }
