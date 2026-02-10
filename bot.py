from __future__ import annotations

import asyncio
import logging
import math
import os
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Tuple

try:
    from telegram import Update
    from telegram.constants import ChatAction
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
except ModuleNotFoundError:  # позволяет запускать unit-тесты без telegram
    Update = object  # type: ignore[assignment]
    ChatAction = type("ChatAction", (), {"TYPING": "typing"})
    Application = CommandHandler = ContextTypes = MessageHandler = filters = None  # type: ignore[assignment]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    total: float
    execution: float
    artistry: float
    difficulty: float
    penalties_total: float
    final_score: float
    penalties_breakdown: Dict[str, float]
    details: Dict[str, float]


@dataclass(frozen=True)
class PenaltyRule:
    code: str
    description: str
    deduction_per_unit: float


class SportAerobicsEvaluator:
    """
    Предварительная автоматическая оценка по видео.

    ВАЖНО: бот не заменяет официальную коллегию судей.
    Но внутри использует более детальные видеометрики (в т.ч. микро-динамику),
    учёт обязательных элементов и штрафный контур.
    """

    MANDATORY_ELEMENTS: List[str] = [
        "push_up",
        "wenson",
        "air_turn",
        "jump_360",
        "high_kick",
        "split_leap",
        "straddle_jump",
        "illusion",
        "support_balance",
        "dynamic_strength",
    ]

    PENALTY_RULES: Dict[str, PenaltyRule] = {
        # Площадка и время
        "out_of_bounds": PenaltyRule("out_of_bounds", "Выход за пределы площадки", 0.5),
        "line_touch": PenaltyRule("line_touch", "Касание линии границы площадки", 0.1),
        "time_violation_minor": PenaltyRule("time_violation_minor", "Нарушение длительности (до 2 сек)", 0.5),
        "time_violation_major": PenaltyRule("time_violation_major", "Нарушение длительности (более 2 сек)", 1.0),
        # Содержание и техника
        "missing_mandatory_element": PenaltyRule("missing_mandatory_element", "Пропуск обязательного элемента", 0.5),
        "incorrect_mandatory_element": PenaltyRule("incorrect_mandatory_element", "Некорректное выполнение обязательного элемента", 0.3),
        "prohibited_element": PenaltyRule("prohibited_element", "Запрещённый элемент", 1.0),
        "prohibited_lift": PenaltyRule("prohibited_lift", "Запрещённая поддержка/подъём", 1.0),
        "fall": PenaltyRule("fall", "Падение спортсмена", 0.5),
        "interruption": PenaltyRule("interruption", "Остановка/срыв композиции", 0.5),
        "coach_assistance": PenaltyRule("coach_assistance", "Посторонняя помощь/подсказка", 1.0),
        # Артистичность и музыка
        "music_tempo_mismatch": PenaltyRule("music_tempo_mismatch", "Несоответствие движения темпу музыки", 0.5),
        "music_cut_or_stop": PenaltyRule("music_cut_or_stop", "Сбой/обрыв музыкального сопровождения", 0.5),
        # Внешний вид и дисциплина
        "attire_violation": PenaltyRule("attire_violation", "Нарушение требований к костюму/внешнему виду", 0.2),
        "sportsmanship_violation": PenaltyRule("sportsmanship_violation", "Нарушение спортивной этики", 0.5),
        "late_entry": PenaltyRule("late_entry", "Опоздание на старт/несвоевременный выход", 0.3),
        "unauthorized_repeat": PenaltyRule("unauthorized_repeat", "Неправомерный повтор упражнения", 1.0),
        # Судейская корректировка
        "manual_judge_adjustment": PenaltyRule("manual_judge_adjustment", "Ручная корректировка судьи", 1.0),
    }

    def evaluate(self, video_path: str, metadata: Dict[str, float] | None = None) -> ScoreResult:
        try:
            import cv2  # локально, чтобы юнит-тесты без opencv могли запускаться
        except ModuleNotFoundError as exc:
            raise RuntimeError("Для анализа видео требуется opencv-python-headless.") from exc

        metadata = metadata or {}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("Не удалось открыть видео.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = frame_count / fps if fps > 0 else 0

        sample_step = max(int(fps // 3), 1)
        frame_idx = 0

        prev_gray = None
        prev_motion = None

        motion_values: List[float] = []
        micro_jerk_values: List[float] = []
        sharpness_values: List[float] = []
        area_values: List[float] = []
        center_x_values: List[float] = []

        while True:
            ok, frame = cap.read()
            if not ok:
                break

            if frame_idx % sample_step != 0:
                frame_idx += 1
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sharpness_values.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))

            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            area = float(binary.mean() / 255.0)
            area_values.append(area)

            moments = cv2.moments(binary)
            if moments["m00"] > 1e-6:
                cx = moments["m10"] / moments["m00"]
                center_x_values.append(float(cx / gray.shape[1]))

            if prev_gray is not None:
                flow = cv2.calcOpticalFlowFarneback(
                    prev_gray,
                    gray,
                    None,
                    0.5,
                    3,
                    15,
                    3,
                    5,
                    1.2,
                    0,
                )
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                motion = float(mag.mean())
                motion_values.append(motion)

                if prev_motion is not None:
                    micro_jerk_values.append(abs(motion - prev_motion))
                prev_motion = motion

            prev_gray = gray
            frame_idx += 1

        cap.release()

        if not sharpness_values:
            raise RuntimeError("Видео слишком короткое или повреждено.")

        avg_motion = self._mean(motion_values)
        motion_std = self._std(motion_values)
        avg_sharpness = self._mean(sharpness_values)
        avg_micro_jerk = self._mean(micro_jerk_values)
        movement_balance = 1.0 - self._std(center_x_values) if center_x_values else 0.0
        movement_balance = self._clamp(movement_balance, 0.0, 1.0)
        area_stability = 1.0 - self._std(area_values) if area_values else 0.0
        area_stability = self._clamp(area_stability, 0.0, 1.0)
        rhythm_consistency = self._rhythm_consistency(motion_values)

        mandatory_bonus, mandatory_missing = self._score_mandatory_elements(metadata)

        execution = self._score_execution(avg_sharpness, motion_std, avg_micro_jerk, movement_balance)
        artistry = self._score_artistry(avg_motion, motion_std, duration, rhythm_consistency)
        difficulty = self._score_difficulty(avg_motion, duration, mandatory_bonus)
        total = round(execution + artistry + difficulty, 2)

        penalties_breakdown = self._compute_penalties(duration=duration, metadata=metadata, mandatory_missing=mandatory_missing)
        penalties_total = round(sum(penalties_breakdown.values()), 2)
        final_score = round(max(total - penalties_total, 0.0), 2)

        return ScoreResult(
            total=total,
            execution=round(execution, 2),
            artistry=round(artistry, 2),
            difficulty=round(difficulty, 2),
            penalties_total=penalties_total,
            final_score=final_score,
            penalties_breakdown=penalties_breakdown,
            details={
                "duration_sec": round(duration, 1),
                "avg_motion": round(avg_motion, 4),
                "motion_std": round(motion_std, 4),
                "avg_micro_jerk": round(avg_micro_jerk, 4),
                "rhythm_consistency": round(rhythm_consistency, 4),
                "movement_balance": round(movement_balance, 4),
                "area_stability": round(area_stability, 4),
                "avg_sharpness": round(avg_sharpness, 2),
                "mandatory_bonus": round(mandatory_bonus, 3),
                "mandatory_missing": float(mandatory_missing),
            },
        )

    def parse_metadata(self, caption: str | None) -> Tuple[Dict[str, float], List[str]]:
        if not caption:
            return {}, []

        parsed: Dict[str, float] = {}
        errors: List[str] = []

        allowed_common = {"mandatory_expected", "mandatory_done", "judge_adjustment"}
        allowed_elements = {f"element_{name}" for name in self.MANDATORY_ELEMENTS}

        chunks = caption.replace("\n", " ").split()
        for chunk in chunks:
            if "=" not in chunk:
                continue
            key, raw_value = chunk.split("=", 1)
            key = key.strip().lower()
            raw_value = raw_value.strip().replace(",", ".")

            if key not in self.PENALTY_RULES and key not in allowed_common and key not in allowed_elements:
                continue

            try:
                parsed[key] = float(raw_value)
            except ValueError:
                errors.append(f"{key}={raw_value}")

        return parsed, errors

    def _score_mandatory_elements(self, metadata: Dict[str, float]) -> Tuple[float, int]:
        total_quality = 0.0
        found = 0

        for name in self.MANDATORY_ELEMENTS:
            key = f"element_{name}"
            if key in metadata:
                quality = self._clamp(metadata[key], 0.0, 1.0)
                total_quality += quality
                found += 1

        if found == 0:
            expected = int(metadata.get("mandatory_expected", len(self.MANDATORY_ELEMENTS)))
            done = int(metadata.get("mandatory_done", 0))
            missing = max(expected - done, 0)
            return 0.0, missing

        avg_quality = total_quality / len(self.MANDATORY_ELEMENTS)
        missing = len(self.MANDATORY_ELEMENTS) - found
        bonus = self._clamp(avg_quality * 2.0, 0.0, 2.0)
        return bonus, missing

    def _compute_penalties(self, duration: float, metadata: Dict[str, float], mandatory_missing: int) -> Dict[str, float]:
        penalties: Dict[str, float] = {}

        if duration < 85 or duration > 95:
            delta = abs(duration - (85 if duration < 85 else 95))
            code = "time_violation_minor" if delta <= 2 else "time_violation_major"
            penalties[code] = round(self.PENALTY_RULES[code].deduction_per_unit, 2)

        if mandatory_missing > 0:
            rule = self.PENALTY_RULES["missing_mandatory_element"]
            penalties[rule.code] = round(mandatory_missing * rule.deduction_per_unit, 2)

        skip_codes = {
            "time_violation_minor",
            "time_violation_major",
            "missing_mandatory_element",
            "manual_judge_adjustment",
        }
        for code, rule in self.PENALTY_RULES.items():
            if code in skip_codes:
                continue
            count = metadata.get(code, 0.0)
            if count > 0:
                penalties[code] = round(count * rule.deduction_per_unit, 2)

        judge_adjustment = metadata.get("judge_adjustment", 0.0)
        if judge_adjustment > 0:
            penalties["manual_judge_adjustment"] = round(judge_adjustment, 2)

        return penalties

    @staticmethod
    def _mean(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _std(values: List[float]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def _rhythm_consistency(self, motion_values: List[float]) -> float:
        if len(motion_values) < 6:
            return 0.0

        mean_motion = self._mean(motion_values)
        if mean_motion <= 1e-9:
            return 0.0

        normalized = [(x - mean_motion) for x in motion_values]
        diffs = [abs(normalized[i] - normalized[i - 1]) for i in range(1, len(normalized))]
        roughness = self._mean(diffs)
        return self._clamp(1.0 - roughness / (mean_motion + 1e-9), 0.0, 1.0)

    def _score_execution(self, sharpness: float, motion_std: float, micro_jerk: float, movement_balance: float) -> float:
        quality = self._clamp((sharpness / 250.0) * 4.5, 0, 4.5)
        control = self._clamp(2.5 - (motion_std / 0.8), 0, 2.5)
        smoothness = self._clamp(2.0 - (micro_jerk / 0.3), 0, 2.0)
        balance = self._clamp(movement_balance * 1.0, 0, 1.0)
        return quality + control + smoothness + balance

    def _score_artistry(self, avg_motion: float, motion_std: float, duration: float, rhythm_consistency: float) -> float:
        dynamic = self._clamp((avg_motion / 2.5) * 4.0, 0, 4.0)
        variation = self._clamp((motion_std / 1.5) * 2.0, 0, 2.0)
        musicality = self._clamp(rhythm_consistency * 2.0, 0, 2.0)
        timing = 2.0 if 85 <= duration <= 95 else 1.0
        return dynamic + variation + musicality + timing

    def _score_difficulty(self, avg_motion: float, duration: float, mandatory_bonus: float) -> float:
        intensity = self._clamp((avg_motion / 2.8) * 5.0, 0, 5.0)
        stamina = self._clamp((duration / 90.0) * 3.0, 0, 3.0)
        elements = self._clamp(mandatory_bonus, 0, 2.0)
        return intensity + stamina + elements


evaluator = SportAerobicsEvaluator()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет! Отправь видео выступления, и я дам детализированную предварительную оценку.\n\n"
        "Можно добавить метаданные в подпись key=value.\n"
        "Пример: out_of_bounds=1 judge_adjustment=0.3 element_push_up=0.9 element_jump_360=0.7\n\n"
        "/penalties — штрафы\n/elements — обязательные элементы\n"
        "Важно: это не заменяет официальный судейский протокол."
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "1) Отправьте видео.\n"
        "2) По желанию добавьте в подпись штрафы и качества элементов.\n"
        "3) Получите E/A/D, штрафы, итог и микро-метрики движения."
    )


async def penalties_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["Доступные штрафы (format: code=count):"]
    for code, rule in evaluator.PENALTY_RULES.items():
        if code == "manual_judge_adjustment":
            lines.append(f"- judge_adjustment=<балл>: {rule.description}")
        else:
            lines.append(f"- {code}: {rule.description} (-{rule.deduction_per_unit})")
    await update.message.reply_text("\n".join(lines))


async def elements_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lines = ["Поддерживаемые обязательные элементы (format: element_<name>=quality_0..1):"]
    lines.extend([f"- element_{name}" for name in evaluator.MANDATORY_ELEMENTS])
    await update.message.reply_text("\n".join(lines))


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.video:
        return

    await message.chat.send_action(action=ChatAction.TYPING)
    video_file = await message.video.get_file()
    metadata, parse_errors = evaluator.parse_metadata(message.caption)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        path = temp_video.name

    try:
        await video_file.download_to_drive(path)
        result = await asyncio.to_thread(evaluator.evaluate, path, metadata)

        penalties_text = "\n".join(
            f"  - {code}: -{value:.2f}" for code, value in sorted(result.penalties_breakdown.items())
        ) or "  - нет"

        response = (
            f"🏅 *Предварительная оценка выступления*\n"
            f"База (E+A+D): *{result.total:.2f} / 30.00*\n"
            f"Штрафы: *-{result.penalties_total:.2f}*\n"
            f"Итог: *{result.final_score:.2f} / 30.00*\n\n"
            f"• Execution (E): *{result.execution:.2f} / 10*\n"
            f"• Artistry (A): *{result.artistry:.2f} / 10*\n"
            f"• Difficulty (D): *{result.difficulty:.2f} / 10*\n\n"
            f"Штрафы:\n{penalties_text}\n\n"
            f"Микро-метрики:\n"
            f"- Длительность: {result.details['duration_sec']} сек\n"
            f"- Средняя динамика: {result.details['avg_motion']}\n"
            f"- Вариативность: {result.details['motion_std']}\n"
            f"- Микро-рывок: {result.details['avg_micro_jerk']}\n"
            f"- Ритмичность: {result.details['rhythm_consistency']}\n"
            f"- Баланс движения: {result.details['movement_balance']}\n"
            f"- Стабильность контура: {result.details['area_stability']}\n"
            f"- Чёткость: {result.details['avg_sharpness']}\n"
            f"- Бонус обязательных: {result.details['mandatory_bonus']}\n"
            f"- Пропущено обязательных: {int(result.details['mandatory_missing'])}"
        )

        if parse_errors:
            response += "\n\n⚠️ Не удалось разобрать: " + ", ".join(parse_errors)

        await message.reply_text(response, parse_mode="Markdown")
    except Exception as exc:
        logger.exception("Ошибка при анализе видео")
        await message.reply_text(f"Не удалось обработать видео: {exc}")
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


async def on_non_video(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text("Пожалуйста, отправьте видео выступления.")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Укажите TELEGRAM_BOT_TOKEN в переменных окружения.")

    if Application is None:
        raise RuntimeError("Установите python-telegram-bot для запуска бота.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("penalties", penalties_command))
    app.add_handler(CommandHandler("elements", elements_command))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(~filters.VIDEO, on_non_video))

    logger.info("Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
