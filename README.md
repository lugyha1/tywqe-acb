# Telegram-бот оценки выступления (спортивная аэробика)

Бот анализирует видео выступления и выдаёт:
- баллы **Execution / Artistry / Difficulty**;
- полный блок **штрафов**;
- итоговый балл;
- расширенные метрики «микро-движений».

> Это автоматическая предварительная оценка. Для официального протокола нужны судьи и утверждённая версия регламента.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export $(cat .env | xargs)
python bot.py
```

## Команды

- `/start`
- `/help`
- `/penalties` — список штрафов
- `/elements` — список обязательных элементов

## Расширенная модель оценки

Бот считает не только «грубую динамику», но и дополнительные признаки:
- `avg_motion` — средняя оптическая динамика;
- `motion_std` — вариативность динамики;
- `avg_micro_jerk` — микро-рывки (кадровый градиент движения);
- `rhythm_consistency` — согласованность ритма;
- `movement_balance` — устойчивость положения по горизонтали;
- `area_stability` — стабильность контура спортсмена;
- `avg_sharpness` — чёткость кадра.

## Обязательные элементы

Поддерживаются ключи вида `element_<name>=quality` (quality от 0 до 1):

- `element_push_up`
- `element_wenson`
- `element_air_turn`
- `element_jump_360`
- `element_high_kick`
- `element_split_leap`
- `element_straddle_jump`
- `element_illusion`
- `element_support_balance`
- `element_dynamic_strength`

Если элементы не переданы явно, можно использовать:
- `mandatory_expected=<число>`
- `mandatory_done=<число>`

## Штрафы (поддерживаемые)

### Площадка и время
- `out_of_bounds`
- `line_touch`
- `time_violation_minor` (авто)
- `time_violation_major` (авто)

### Элементы и техника
- `missing_mandatory_element` (авто)
- `incorrect_mandatory_element`
- `prohibited_element`
- `prohibited_lift`
- `fall`
- `interruption`
- `coach_assistance`

### Музыка и артистичность
- `music_tempo_mismatch`
- `music_cut_or_stop`

### Внешний вид и дисциплина
- `attire_violation`
- `sportsmanship_violation`
- `late_entry`
- `unauthorized_repeat`

### Ручная судейская корректировка
- `judge_adjustment`

## Пример подписи к видео

```text
out_of_bounds=1 line_touch=2 judge_adjustment=0.2 \
element_push_up=0.9 element_jump_360=0.8 element_split_leap=0.7
```

## Важно про «100% точность»

В код добавлены все элементы и штрафы, поддерживаемые текущей конфигурацией проекта.
Чтобы получить 100% совпадение с вашей официальной версией правил, актуализируйте коэффициенты и перечни в `SportAerobicsEvaluator.PENALTY_RULES` и `SportAerobicsEvaluator.MANDATORY_ELEMENTS` под конкретный регламент/категорию.

## Тесты

```bash
python -m py_compile bot.py tests/test_evaluator.py
pytest -q
```
