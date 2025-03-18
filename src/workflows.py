import datetime
import logging

import pandas as pd


from src.app.db.adapter import Database

from src.data import summary_activity_to_activity_model
from src.gemini import generate_activity_name_with_gemini

from src.strava import (
    fetch_activity_data,
    get_strava_client,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rename_workflow(
    activity_id: int,
    access_token: str,
    refresh_token: str,
    expires_at: int,
    client_id: int,
    client_secret: str,
    gemini_api_key: str,
    pushbullet_api_key: str,
    postgres_connection_string: str,
    encryption_key: bytes,
):
    time_start = datetime.datetime.now()

    days = 365
    temperature = 2

    description_to_append = "named with NeuralTag 🤖"

    client = get_strava_client(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        strava_client_id=client_id,
        strava_client_secret=client_secret,
    )

    activity = fetch_activity_data(
        client=client,
        activity_id=activity_id,
    )

    existing_description = activity.description
    activity = summary_activity_to_activity_model(activity)

    if description_to_append in str(existing_description) and activity.name != "Rename":
        logger.info(f"Activity {activity_id} already named")
        return

    db = Database(
        connection_string=postgres_connection_string,
        encryption_key=encryption_key,
    )

    before = activity.start_date_local + datetime.timedelta(days=1)
    after = before - datetime.timedelta(days=days)
    activities = db.get_activities_by_date_range(
        athlete_id=activity.athlete_id, before=before, after=after
    )

    activities = [activity] + activities

    activities_df = pd.DataFrame([activity.dict() for activity in activities])

    columns = [
        "activity_id",
        "date",
        "time",
        "day_of_week",
        "name",
        "average_heartrate",
        "max_heartrate",
        "total_elevation_gain",
        "weighted_average_watts",
        "moving_time_minutes",
        "distance_km",
        "sport_type",
        "start_lat",
        "start_lng",
        "end_lat",
        "end_lng",
        "pace_min_per_km",
        "map_centroid_lat",
        "map_centroid_lon",
        "map_area",
    ]

    activities_df = activities_df[activities_df["sport_type"] == activity.sport_type]

    activities_df = activities_df[columns]
    activities_df = activities_df.dropna(axis=1, how="all")

    activities_df = activities_df.rename({"activity_id": "id"}, axis=1)

    name_results = generate_activity_name_with_gemini(
        activity_id=activity_id,
        data=activities_df,
        number_of_options=3,
        api_key=gemini_api_key,
        temperature=temperature,
    )
    logger.info(f"Name suggestions: {name_results}")

    top_name_suggestion = name_results[0].name
    top_name_description = name_results[0].description
    logger.info(
        f"Top name suggestion for activity {activity_id}: {top_name_suggestion}: {top_name_description}"
    )

    time_end = datetime.datetime.now()
    duration_seconds = (time_end - time_start).total_seconds()
    logger.info(f"Duration: {duration_seconds} seconds")

    if existing_description is None:
        existing_description = ""

    if description_to_append not in str(existing_description):
        new_description = f"{existing_description}\n\n{description_to_append}".strip()
    else:
        new_description = existing_description
    logger.info(f"New description: {new_description}")

    # client.update_activity(
    #     activity_id=activity_id,
    #     name=top_name_suggestion,
    #     description=new_description,
    # )

    # # notify via pushbullet
    # pb = Pushbullet(pushbullet_api_key)
    # pb.push_note(title=top_name_suggestion, body=top_name_description)
