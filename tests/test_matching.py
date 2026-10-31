import math
import pytest
from backend.catalog import PROJECT_BANKS,PROJECTS,public_project
from models.quiz_data import QUESTIONS
from models.mood_axes import MOOD_AXES
from logic.scoring import calculate_mood
from logic.matcher import score_project,get_candidates,spin_wheel

def test_catalogue_integrity():
    assert sum(map(len,PROJECT_BANKS.values()))==len(PROJECTS)==275
    for specialty,bank in PROJECT_BANKS.items():
        assert len(bank)==55
        for p in bank:
            assert p['specialty']==specialty
            assert p['difficulty'] in ('easy','medium','hard')
            assert set(p['mood_fit'])==set(MOOD_AXES)
            assert all(type(v) is int and -2<=v<=2 for v in p['mood_fit'].values())
            assert all(p.get(k) for k in ('id','title','description','tech_stack','steps','stretch_goals'))
            assert public_project(p)['plan_quality'] in ('outline','detailed')

def test_scoring_clamps_axes():
    effects=[q['options'][-1]['effect'] for q in QUESTIONS]
    mood=calculate_mood(effects)
    assert set(mood)==set(MOOD_AXES)
    assert all(-2<=v<=2 for v in mood.values())
    assert calculate_mood([{'unknown':999}])==dict(energy=0,creativity=0,challenge=0)

@pytest.mark.parametrize('specialty',PROJECT_BANKS)
@pytest.mark.parametrize('difficulty',['easy','medium','hard'])
def test_matching_all_specialty_difficulty_paths(specialty,difficulty):
    mood=dict(energy=-1,creativity=1,challenge=0)
    candidates=get_candidates(mood,difficulty,PROJECT_BANKS[specialty])
    assert len(candidates)==5
    scores=[score_project(mood,p) for p in candidates]
    assert scores==sorted(scores)
    assert all(p['difficulty']==difficulty for p in candidates)
    assert spin_wheel(candidates,mood) in candidates

def test_weighted_selection_uses_inverse_distance(monkeypatch):
    from logic import matcher
    mood=dict(energy=0,creativity=0,challenge=0)
    projects=[{'mood_fit':mood},{'mood_fit':dict(energy=2,creativity=0,challenge=0)}]
    seen={}
    def choices(population,weights,k):seen['weights']=weights;return [population[0]]
    monkeypatch.setattr(matcher.random,'choices',choices)
    assert spin_wheel(projects,mood) is projects[0]
    assert seen['weights']==[2,0.4]
    assert spin_wheel([],mood) is None

def test_generic_templates_are_not_mislabelled_as_detailed():
    from collections import Counter
    counts=Counter(public_project(p)['plan_quality'] for p in PROJECTS.values())
    assert counts=={'outline':265,'detailed':10}
    assert all(public_project(p)['plan_quality']=='outline' for p in PROJECT_BANKS['azure'])
