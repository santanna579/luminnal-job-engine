from app.schemas.match import MatchProfile, MatchJob, MatchPreviewResponse, MatchDetailScores


def calculate_match_score(profile: MatchProfile, job: MatchJob) -> MatchPreviewResponse:

    skills_profile = [s.lower() for s in profile.skills]
    job_desc = job.description.lower()

    matched = [s for s in skills_profile if s in job_desc]
    gaps = [s for s in ["python", "sql", "etl", "aws"] if s not in skills_profile]

    skills_score = min(len(matched) * 20, 100)
    experience_score = 70 if profile.experience else 30
    semantic_score = 60

    final_score = int(
        (skills_score * 0.4) +
        (experience_score * 0.3) +
        (semantic_score * 0.3)
    )

    return MatchPreviewResponse(
        score=final_score,
        summary=f"{len(matched)} skills relevantes encontradas",
        strengths=matched[:5],
        gaps=gaps[:5],
        suggestions=[],
        details=MatchDetailScores(
            skills_score=skills_score,
            experience_score=experience_score,
            semantic_score=semantic_score
        )
    )