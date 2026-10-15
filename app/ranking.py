
def rank_jobs(jobs, candidate_skills):
    if not isinstance(jobs, list):
        raise ValueError("jobs must be a list")

    if not isinstance(candidate_skills, list):
        raise ValueError("candidate_skills must be a list")

    if not candidate_skills:
        raise ValueError("Candidate skill data is missing")

    normalized_skills = {
        skill.strip().lower()
        for skill in candidate_skills
        if isinstance(skill, str) and skill.strip()
    }

    ranked_jobs = []

    for job in jobs:
        required_skills = job.get("required_skills", [])

        if not isinstance(required_skills, list):
            raise ValueError("required_skills must be a list")

        normalized_required = {
            skill.strip().lower()
            for skill in required_skills
            if isinstance(skill, str) and skill.strip()
        }

        matched = normalized_skills & normalized_required

        score = (
            len(matched) / len(normalized_required)
            if normalized_required
            else 0.0
        )

        ranked_jobs.append({
            "title": job.get("title", "Unknown"),
            "match_score": round(score, 2),
            "matched_skills": sorted(matched),
        })

    return sorted(
        ranked_jobs,
        key=lambda job: job["match_score"],
        reverse=True,
    )
