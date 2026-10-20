#!/usr/bin/env python3
"""Generate DOCX: hardware impact + cloud server research for STT App."""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "docs" / "_research_figures"
OUTPUT = ROOT / "docs" / "STT_Issledovanie_Proizvoditelnost_i_Servery.docx"

# Illustrative estimates for 30-minute mixed RU/EN dialog, faster-whisper + diarization.
# Not benchmarks from this repo — label clearly in the document.


def _style_doc(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)


def _h(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def _p(doc: Document, text: str) -> None:
    doc.add_paragraph(text)


def _bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def _table(doc: Document, headers: list[str], rows: list[list[str]]) -> None:
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        t.rows[0].cells[i].text = h
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            t.rows[ri + 1].cells[ci].text = val


def _add_figure(doc: Document, path: Path, width_in: float = 5.8, caption: str = "") -> None:
    doc.add_picture(str(path), width=Inches(width_in))
    if caption:
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.runs[0].italic = True
        cap.runs[0].font.size = Pt(10)


def chart_processing_time_30min() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    labels = [
        "MacBook Air\nM1 CPU\nmedium",
        "MacBook Pro\nM2 CPU\nmedium",
        "VPS 8 vCPU\nx86\nmedium",
        "VPS 16 vCPU\nx86\nlarge-v3",
        "GPU T4\nlarge-v3",
        "GPU RTX 4090\nlarge-v3",
    ]
    # Minutes to process 30 min of audio (estimate band: use midpoint)
    minutes = np.array([55, 45, 70, 50, 8, 4])
    err = np.array([15, 12, 20, 15, 3, 2])

    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#5b9dff", "#5b9dff", "#7ab0ff", "#7ab0ff", "#3d8bfd", "#1e6fe8"]
    x = np.arange(len(labels))
    ax.bar(x, minutes, yerr=err, capsize=4, color=colors, edgecolor="#2a3348")
    ax.axhline(30, color="#ff6b7a", linestyle="--", linewidth=1, label="Длина файла (30 мин)")
    ax.set_ylabel("Время обработки (мин)")
    ax.set_title("Оценка времени обработки 30-минутного файла по конфигурациям")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "chart_processing_time.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_rtf_by_config() -> Path:
    """Real-time factor (audio_min / wall_min) — higher is better."""
    labels = ["M1 CPU\nmedium", "8 vCPU\nmedium", "16 vCPU\nlarge", "T4 GPU\nlarge", "4090\nlarge"]
    rtf = np.array([0.55, 0.43, 0.60, 3.8, 7.5])
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(labels, rtf, color="#5b9dff")
    ax.set_xlabel("Real-Time Factor (× realtime)")
    ax.set_title("Относительная скорость ASR (выше — быстрее)")
    ax.axvline(1.0, color="#ff6b7a", linestyle="--", label="1× realtime")
    ax.legend(fontsize=8)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "chart_rtf.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_pipeline_share() -> Path:
    stages = ["ffmpeg", "ASR\n(Whisper)", "Diarization\n(Resemblyzer)", "Merge / IO"]
    # Typical share on CPU-bound Mac, 30 min file
    share = [3, 82, 13, 2]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(
        share,
        labels=stages,
        autopct="%1.0f%%",
        startangle=90,
        colors=["#9aa7bd", "#5b9dff", "#7ab0ff", "#2a3348"],
    )
    ax.set_title("Доля времени этапов (CPU, medium, ~30 мин)")
    fig.tight_layout()
    out = FIG_DIR / "chart_pipeline_pie.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_ram_vram() -> Path:
    configs = ["medium\nCPU", "large-v3\nCPU", "large-v3\nGPU int8", "large-v3\nGPU fp16"]
    ram_gb = [4, 10, 6, 8]
    vram_gb = [0, 0, 5, 9]
    x = np.arange(len(configs))
    w = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(x - w / 2, ram_gb, w, label="RAM (системная)", color="#5b9dff")
    ax.bar(x + w / 2, vram_gb, w, label="VRAM (GPU)", color="#3d8bfd")
    ax.set_ylabel("ГБ (оценка пика)")
    ax.set_title("Потребление памяти по конфигурации модели")
    ax.set_xticks(x)
    ax.set_xticklabels(configs)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "chart_memory.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_cloud_cost_per_job() -> Path:
    providers = ["Hetzner\nCPU VPS", "DO Premium\nCPU", "AWS\ng4dn.xlarge", "RunPod\nT4", "RunPod\n4090", "Lambda\nA10"]
    cost_usd = [0.04, 0.08, 0.35, 0.06, 0.12, 0.15]  # est $ per 30-min job
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(providers, cost_usd, color="#5b9dff", edgecolor="#1a2030")
    ax.set_ylabel("USD за один файл (~30 мин)")
    ax.set_title("Ориентировочная стоимость обработки одного job (оценка)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "chart_cloud_cost.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_price_quality_scatter() -> Path:
    # x = $/hour instance, y = speed score 1-10
    names = ["Hetzner CCX", "DO 8vCPU", "AWS g4dn", "RunPod T4", "RunPod 4090", "Lambda A10"]
    hourly = [0.06, 0.12, 0.52, 0.25, 0.44, 0.60]
    score = [2.5, 3.0, 6.5, 6.0, 9.0, 7.5]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(hourly, score, s=120, c="#5b9dff", edgecolors="#1a2030", zorder=3)
    for i, n in enumerate(names):
        ax.annotate(n, (hourly[i], score[i]), textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax.set_xlabel("Цена инстанса (USD/час, порядок величины)")
    ax.set_ylabel("Условная скорость обработки (1–10)")
    ax.set_title("Цена vs скорость: GPU-класс обычно лучший баланс для ASR")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIG_DIR / "chart_price_quality.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def build_document(figs: dict[str, Path]) -> Document:
    doc = Document()
    _style_doc(doc)

    t = doc.add_heading(
        "Исследование: влияние железа на скорость STT App и выбор сервера",
        0,
    )
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _p(
        doc,
        "Проект: my_stt_app (faster-whisper + диarization Resemblyzer/pyannote). "
        "Документ носит аналитико-справочный характер: цифры — оценочные модели для "
        "планирования инфраструктуры. Перед продакшеном рекомендуется собственный бенчмарк "
        "на 3–5 репрезентативных файлах.",
    )

    _h(doc, "Часть A. Влияние CPU, RAM и VRAM на скорость", 1)

    _h(doc, "A.1. Пайплайн и узкие места", 2)
    _p(
        doc,
        "Обработка одного файла включает: (1) ffmpeg — нормализация в mono 16 kHz; "
        "(2) ASR faster-whisper — основная нагрузка; (3) диarization — Resemblyzer (CPU) "
        "или pyannote (CPU/GPU); (4) слияние сегментов и запись в SQLite. "
        "На типичной CPU-конфигурации с моделью medium **80–90% wall-time** занимает ASR.",
    )
    _add_figure(doc, figs["pipeline"], caption="Рис. 1. Распределение времени этапов (оценка, CPU medium).")

    _h(doc, "A.2. Процессор (CPU)", 2)
    _p(
        doc,
        "Whisper на CPU (int8 через faster-whisper) масштабируется числом физических ядер "
        "и SIMD (AVX2/AVX-512 на x86, NEON на ARM). Apple Silicon (M1/M2/M3) даёт хорошую "
        "энергоэффективность, но для large-v3 на CPU всё равно длинные очереди.",
    )
    _table(
        doc,
        ["Конфигурация CPU", "Модель", "RTF (× realtime)", "30 мин аудио → wall-time"],
        [
            ["Apple M1, 8 GB, 4P+4E", "medium int8", "0.4–0.7", "~45–75 мин"],
            ["Apple M2/M3 Pro", "medium int8", "0.5–0.9", "~35–60 мин"],
            ["x86 VPS 8 vCPU", "medium int8", "0.3–0.6", "~50–100 мин"],
            ["x86 16 vCPU dedicated", "large-v3 int8", "0.4–0.8", "~40–75 мин"],
            ["GPU T4 + CUDA", "large-v3", "3–8", "~4–10 мин"],
            ["GPU RTX 4090", "large-v3", "6–15", "~2–5 мин"],
        ],
    )
    doc.add_paragraph()
    _p(doc, "RTF (Real-Time Factor) = длительность_аудио / время_обработки. RTF=2 означает «30 мин за 15 мин».")
    _add_figure(doc, figs["rtf"], caption="Рис. 2. Сравнение RTF по классам железа (оценка).")
    _add_figure(doc, figs["time30"], caption="Рис. 3. Время обработки 30-минутного файла.")

    _h(doc, "A.3. Оперативная память (RAM)", 2)
    _bullets(
        doc,
        [
            "faster-whisper medium int8: ~2–4 GB RAM в пике на процесс.",
            "large-v3 int8 на CPU: ~6–10 GB RAM.",
            "PyTorch + pyannote: дополнительно ~2–4 GB при первом запуске pipeline.",
            "Resemblyzer + sklearn: +0.5–1.5 GB в зависимости от числа сегментов.",
            "Рекомендация для CPU-only сервера: **минимум 16 GB**, комфортно **32 GB** при large-v3 и параллельных зависимостях.",
            "Swap на SSD сильно убивает RTF — избегать конфигураций с 8 GB для large-v3.",
        ],
    )
    _add_figure(doc, figs["memory"], caption="Рис. 4. Оценка пикового RAM/VRAM.")

    _h(doc, "A.4. Видеопамять (VRAM) и GPU", 2)
    _p(
        doc,
        "GPU ускоряет прежде всего **ASR**. Диarization pyannote на GPU возможна, но на Mac MPS "
        "исторически нестабильна; на Linux+CUDA — целесообразна. VRAM определяет максимальный "
        "размер модели и batch:",
    )
    _table(
        doc,
        ["VRAM", "Модель Whisper", "compute_type", "Комментарий"],
        [
            ["≤4 GB", "small / medium", "int8 / fp16", "Tight fit, риск OOM на long batch"],
            ["8 GB", "medium, distil-large", "fp16", "Оптимально для MVP GPU"],
            ["16 GB (T4)", "large-v3", "int8 / fp16", "Рекомендуемый класс для качества"],
            ["24 GB+", "large-v3", "fp16", "Запас для pyannote на GPU, несколько worker"],
        ],
    )

    _h(doc, "A.5. Практические выводы по железу", 2)
    _bullets(
        doc,
        [
            "Локальный Mac + medium CPU — OK для личного use и прототипа, не для очереди клиентов.",
            "Для качества large-v3 без GPU ждать **~1× realtime и хуже** — плохой UX при 30-мин лимите.",
            "GPU класса T4 / L4 / RTX 4060–4090 — основной рычаг сокращения времени ASR.",
            "RAM важнее CPU count после 8 vCPU для single-job MVP (один worker).",
            "Диск: SSD для data/uploads и кэша HF; NVMe снижает простой при IO ffmpeg.",
        ],
    )

    doc.add_page_break()
    _h(doc, "Часть B. Выбор арендуемого сервера (цена/качество)", 1)

    _h(doc, "B.1. Профиль нагрузки STT App", 2)
    _p(
        doc,
        "Текущая архитектура: **один ML-worker на процесс**, локальный SQLite, stateless frontend. "
        "Типичный job: до 30 мин аудио, CPU/GPU burst 5–90 мин. Для публичного сервиса нужны: "
        "GPU для ASR, 16–32 GB RAM, 4+ vCPU для ffmpeg и API, диск 50–200 GB под uploads + cache моделей.",
    )

    _h(doc, "B.2. Классы провайдеров", 2)
    _table(
        doc,
        ["Класс", "Примеры", "Плюсы", "Минусы для STT"],
        [
            ["Budget CPU VPS", "Hetzner, DigitalOcean", "Дёшево", "Очень медленный ASR"],
            ["CPU cloud", "AWS m6i, GCP n2", "Стабильность, SLA", "Плохой $/RTF для Whisper"],
            ["GPU IaaS", "AWS g4dn/g5, GCP L4", "Предсказуемость", "Дороже spot GPU"],
            ["GPU marketplace", "RunPod, Vast.ai", "Низкий $/GPU-час", "Spot/preempt, вариативность"],
            ["ML-focused", "Lambda Labs, CoreWeave", "GPU + образы ML", "Меньше регионов"],
        ],
    )

    _h(doc, "B.3. Сравнительная таблица (оценка на Q4 2025 — уточнять на сайтах)", 2)
    _table(
        doc,
        ["Провайдер / тариф", "GPU / CPU", "~USD/час", "30 мин job", "~USD/job", "Рекомендация"],
        [
            ["Hetzner CCX23", "8 vCPU, 32 GB", "0.05", "60–90 мин", "0.05–0.08", "Dev, не prod ASR"],
            ["DO Premium 8vCPU", "8 vCPU, 16 GB", "0.12", "50–80 мин", "0.10–0.16", "API + очередь, ASR медленно"],
            ["AWS g4dn.xlarge", "T4 16 GB", "0.52", "5–10 мин", "0.04–0.09", "Enterprise SLA"],
            ["RunPod T4", "T4 16 GB", "0.20–0.35", "4–8 мин", "0.01–0.05", "Лучший баланс MVP"],
            ["RunPod RTX 4090", "24 GB", "0.34–0.69", "2–5 мин", "0.01–0.06", "Max speed, spot риск"],
            ["Lambda A10", "24 GB", "0.60", "3–6 мин", "0.03–0.06", "Стабильный ML-host"],
        ],
    )
    _add_figure(doc, figs["cost"], caption="Рис. 5. Ориентировочная стоимость одного 30-мин job.")
    _add_figure(doc, figs["scatter"], caption="Рис. 6. Цена инстанса vs условная скорость.")

    _h(doc, "B.4. Рекомендуемая топология для «макс. цена/качество»", 2)
    _p(doc, "Схема разделения (текстовая диаграмма):")
    _p(
        doc,
        "[Пользователь] → [CDN/Reverse proxy Nginx]\n"
        "                      ↓\n"
        "              [CPU VPS 2–4 vCPU] — FastAPI, SQLite/Postgres, Redis queue (будущее)\n"
        "                      ↓ (job queue)\n"
        "              [GPU worker RunPod/Lambda] — faster-whisper large-v3 + diarization\n"
        "                      ↓\n"
        "              [Object storage S3/R2] — uploads (опционально)",
    )

    _h(doc, "B.5. Итоговые рекомендации", 2)
    _table(
        doc,
        ["Сценарий", "Рекомендация"],
        [
            ["Личный Mac / прототип", "Оставить CPU medium; HF optional"],
            ["MVP 1–5 пользователей/день", "RunPod T4 on-demand + маленький Hetzner API"],
            ["Production SLA", "AWS g5/g4dn или Lambda + managed DB, autoscale 0 GPU"],
            ["Минимальный бюджет", "CPU VPS только если UX «ждать час+» приемлем"],
            ["Максимальное качество/скорость", "RTX 4090 / A10 + large-v3 fp16"],
        ],
    )

    _h(doc, "B.6. Риски и как их снять", 2)
    _bullets(
        doc,
        [
            "Spot/preempt GPU — checkpoint job stage в SQLite, retry ASR.",
            "Cold start моделей — warm container, preload Whisper при старте worker.",
            "Privacy (локальный продукт) — self-host GPU в EU (Hetzner GPU, OVH) vs US cloud.",
            "Скрытые costs: egress трафик uploads, хранение HF cache ~5–15 GB.",
        ],
    )

    _h(doc, "Приложение: как провести свой бенчмарк", 2)
    _bullets(
        doc,
        [
            "3 файла: 5 мин RU dialog, 5 min EN, 30 min mixed.",
            "CLI: python scripts/transcribe_cli.py file -o out.json, замер wall-time.",
            "Фиксировать: WHISPER_MODEL, device, compute_type, DIARIZATION_BACKEND.",
            "Заполнить таблицы RTF реальными числами и обновить данный документ.",
        ],
    )

    _p(
        doc,
        "Дисклеймер: цены облаков меняются; перед закупкой сверить актуальные тарифы и "
        "доступность GPU в нужном регионе (EU/RU compliance).",
    )

    return doc


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figs = {
        "pipeline": chart_pipeline_share(),
        "rtf": chart_rtf_by_config(),
        "time30": chart_processing_time_30min(),
        "memory": chart_ram_vram(),
        "cost": chart_cloud_cost_per_job(),
        "scatter": chart_price_quality_scatter(),
    }
    doc = build_document(figs)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    print(f"Written: {OUTPUT}")


if __name__ == "__main__":
    main()
