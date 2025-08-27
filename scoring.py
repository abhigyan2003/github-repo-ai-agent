from dataclasses import dataclass


@dataclass
class ScoreBreakdown:
    readme: float
    health: float
    activity: float
    engagement: float
    community: float


def normalize_0_10(value_0_1: float) -> float:
    value_0_1 = max(0.0, min(1.0, value_0_1))
    return round(value_0_1 * 10, 2)


def compute_overall_score(
    readme_quality: float,
    health_score: float,
    activity_score: float,
    engagement_score: float,
    closed_issue_ratio: float,
) -> tuple[float, ScoreBreakdown]:
    # Weighted composite
    w_readme = 0.15
    w_health = 0.30
    w_activity = 0.30
    w_engagement = 0.10
    w_community = 0.15

    community = max(0.0, min(1.0, closed_issue_ratio))
    composite = (
        readme_quality * w_readme
        + health_score * w_health
        + activity_score * w_activity
        + engagement_score * w_engagement
        + community * w_community
    )
    return (
        normalize_0_10(composite),
        ScoreBreakdown(
            readme=normalize_0_10(readme_quality),
            health=normalize_0_10(health_score),
            activity=normalize_0_10(activity_score),
            engagement=normalize_0_10(engagement_score),
            community=normalize_0_10(community),
        ),
    )


