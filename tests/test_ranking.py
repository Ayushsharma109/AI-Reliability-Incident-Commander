
import pytest

from app.ranking import rank_jobs


def test_jobs_are_ranked_by_skill_match():
    jobs = [
        {
            "title": "ML Intern",
            "required_skills": ["Python", "SQL", "Docker"],
        },
        {
            "title": "Python Intern",
            "required_skills": ["Python", "SQL"],
        },
    ]

    result = rank_jobs(jobs, ["Python", "SQL"])

    assert result[0]["title"] == "Python Intern"
    assert result[0]["match_score"] == 1.0
    assert result[1]["match_score"] == pytest.approx(2 / 3, abs=0.01)


def test_missing_candidate_skills_raise_error():
    with pytest.raises(
        ValueError,
        match="Candidate skill data is missing",
    ):
        rank_jobs(
            [{"title": "AI Intern", "required_skills": ["Python"]}],
            [],
        )


def test_invalid_jobs_input_is_rejected():
    with pytest.raises(ValueError, match="jobs must be a list"):
        rank_jobs("not a list", ["Python"])
