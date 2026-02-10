from bot import SportAerobicsEvaluator


def test_clamp_bounds():
    evaluator = SportAerobicsEvaluator()
    assert evaluator._clamp(5, 0, 3) == 3
    assert evaluator._clamp(-1, 0, 3) == 0
    assert evaluator._clamp(2, 0, 3) == 2


def test_score_ranges():
    evaluator = SportAerobicsEvaluator()

    e = evaluator._score_execution(sharpness=800, motion_std=0.4, micro_jerk=0.1, movement_balance=0.8)
    a = evaluator._score_artistry(avg_motion=2.0, motion_std=1.0, duration=90, rhythm_consistency=0.8)
    d = evaluator._score_difficulty(avg_motion=2.5, duration=90, mandatory_bonus=1.5)

    assert 0 <= e <= 10
    assert 0 <= a <= 10
    assert 0 <= d <= 10


def test_parse_metadata_with_elements_and_penalties():
    evaluator = SportAerobicsEvaluator()
    metadata, errors = evaluator.parse_metadata(
        "out_of_bounds=2 music_tempo_mismatch=1 judge_adjustment=0.4 element_push_up=0.9 element_jump_360=0.7"
    )

    assert not errors
    assert metadata["out_of_bounds"] == 2
    assert metadata["music_tempo_mismatch"] == 1
    assert metadata["judge_adjustment"] == 0.4
    assert metadata["element_push_up"] == 0.9


def test_mandatory_bonus_and_missing_penalty():
    evaluator = SportAerobicsEvaluator()

    metadata = {
        "element_push_up": 1.0,
        "element_jump_360": 0.8,
        "out_of_bounds": 1.0,
        "judge_adjustment": 0.3,
    }

    bonus, missing = evaluator._score_mandatory_elements(metadata)
    penalties = evaluator._compute_penalties(duration=100, metadata=metadata, mandatory_missing=missing)

    assert 0 <= bonus <= 2.0
    assert missing == len(evaluator.MANDATORY_ELEMENTS) - 2
    assert penalties["time_violation_major"] == 1.0
    assert penalties["missing_mandatory_element"] == round(missing * 0.5, 2)
    assert penalties["out_of_bounds"] == 0.5
    assert penalties["manual_judge_adjustment"] == 0.3
