"""
MIT License

Copyright (c) 2017 - Present PythonistaGuild

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from twitchio.user import PartialUser
from twitchio.utils import parse_timestamp


if TYPE_CHECKING:
    import datetime

    from twitchio.http import HTTPClient
    from twitchio.types_.responses import (
        PredictionsResponseData,
        PredictionsResponseOutcomes,
        PredictionsResponseTopPredictors,
    )

__all__ = ("Prediction", "PredictionOutcome", "Predictor")


class Prediction:
    """
    Represents a Prediction

    | Status      | Description |
    | ----------- | ----------- |
    | ACTIVE      | The Prediction is running and viewers can make predictions.   |
    | CANCELED    | The broadcaster canceled the Prediction and refunded the Channel Points to the participants.  |
    | LOCKED      | The broadcaster locked the Prediction, which means viewers can no longer make predictions.    |
    | RESOLVED    | The winning outcome was determined and the Channel Points were distributed to the viewers who predicted the correct outcome.   |


    Attributes
    ----------
    id: str
        An ID that identifies this prediction.
    broadcaster: PartialUser
        The broadcaster that created the prediction.
    title: str
        The question that the prediction asks.
    winning_outcome_id: str | None
        The ID of the winning outcome. Is None unless status is RESOLVED.
    outcomes: list[PredictionOutcome]
        The list of possible outcomes for the prediction.
    prediction_window: int
        The length of time (in seconds) that the prediction will run for.
    created_at: datetime.datetime
        The datetime of when the prediction began.
    ended_at: datetime.datetime | None
        The datetime of when the prediction ended. This is None if status is `ACTIVE`.
    locked_at: datetime.datetime | None
        The datetime of when the prediction locked. If status is not `LOCKED`, this is set to None.
    """

    __slots__ = (
        "_http",
        "id",
        "broadcaster",
        "title",
        "winning_outcome_id",
        "outcomes",
        "prediction_window",
        "status",
        "created_at",
        "ended_at",
        "locked_at",
    )

    def __init__(self, data: PredictionsResponseData, *, http: HTTPClient) -> None:
        self._http = http
        self.id: str = data["id"]
        self.broadcaster: PartialUser = PartialUser(data["broadcaster_id"], data["broadcaster_login"], http=http)
        self.title: str = data["title"]
        self.winning_outcome_id: str | None = data["winning_outcome_id"] or None
        self.outcomes: list[PredictionOutcome] = [PredictionOutcome(c, http=self._http) for c in data["outcomes"]]
        self.prediction_window: int = int(data["prediction_window"])
        self.status: Literal["ACTIVE", "CANCELED", "LOCKED", "RESOLVED"] = data["status"]
        self.created_at: datetime.datetime = parse_timestamp(data["created_at"])
        _ended_at = data.get("ended_at")
        self.ended_at: datetime.datetime | None = parse_timestamp(_ended_at) if _ended_at else None
        _locked_at = data.get("locked_at")
        self.ended_at: datetime.datetime | None = parse_timestamp(_locked_at) if _locked_at else None

    def __repr__(self) -> str:
        return f"<Prediction id={self.id} title={self.title} status={self.status} created_at={self.created_at}>"

    async def end_prediction(
        self,
        *,
        status: Literal["RESOLVED", "CANCELED", "LOCKED"],
        token_for: str,
        winning_outcome_id: str | None = None,
    ) -> Prediction:
        """
        End an active prediction.

        Parameters
        ----------
        status  Literal["RESOLVED", "CANCELED", "LOCKED"]
            The status to set the prediction to. Possible case-sensitive values are: `RESOLVED`, `CANCELED`, `LOCKED`
        token_for: str
            User access token that includes the `channel:manage:predictions` scope.

        Returns
        -------
        Prediction
            A Prediction object.
        """
        data = await self._http.patch_prediction(
            broadcaster_id=self.broadcaster.id,
            id=self.id,
            status=status,
            token_for=token_for,
            winning_outcome_id=winning_outcome_id,
        )
        return Prediction(data["data"][0], http=self._http)


class PredictionOutcome:
    """
    Represents a prediction outcome.

    Attributes
    ----------
    id: str
        An ID that identifies the choice.
    title: str
        The choice's title.
    users: int
        The number of unique viewers that chose this outcome.
    channel_points: int
        The number of Channel Points spent by viewers on this outcome.
    top_predictors: int
        A list of viewers who were the top predictors; otherwise, None if none.
    color: Literal["BLUE", "PINK"]
        The number of votes cast using Channel Points.
    """

    __slots__ = ("id", "title", "color", "channel_points", "users", "top_predictors")

    def __init__(self, data: PredictionsResponseOutcomes, *, http: HTTPClient) -> None:
        self.id: str = data["id"]
        self.title: str = data["title"]
        self.users: int = int(data["users"])
        self.channel_points: int = int(data["channel_points"])
        self.color: str = data["color"]
        self.top_predictors: list[Predictor] | None = (
            [Predictor(d, http=http) for d in data["top_predictors"]] if data["top_predictors"] else None
        )

    @property
    def colour(self) -> str:
        """The colour of the prediction. Alias to color."""
        return self.color

    def __repr__(self) -> str:
        return f"<PredictionOutcome id={self.id} title={self.title} channel_points={self.channel_points}>"


class Predictor:
    """
    Represents a predictor

    Attributes
    -----------
    user: PartialUser
        The viewer.
    channel_points_used: int
        Number of Channel Points used by the user.
    channel_points_won: int
        Number of Channel Points won by the user.
    """

    __slots__ = ("channel_points_used", "channel_points_won", "user")

    def __init__(self, data: PredictionsResponseTopPredictors, *, http: HTTPClient) -> None:
        self.channel_points_used: int = data["channel_points_used"]
        self.channel_points_won: int = data["channel_points_won"]
        self.user = PartialUser(data["user_id"], data["user_login"], http=http)

    def __repr__(self) -> str:
        return f"<Predictor user={self.user} channel_points_used={self.channel_points_used} channel_points_won={self.channel_points_won}>"