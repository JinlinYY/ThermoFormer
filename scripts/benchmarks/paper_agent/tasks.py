"""A frozen within-system pilot, not a claim of unseen-system generalization."""

from paper_agent.contracts import PaperTask


def pilot_tasks() -> list[PaperTask]:
    tasks = []
    for i, (feed, purity, recovery, stages, reflux) in enumerate(
        [
            (0.466, 0.995, 0.98, 13, 3),
            (0.466, 0.995, 0.98, 12, 3),
            (0.466, 0.995, 0.98, 10, 3),
            (0.466, 0.995, 0.98, 8, 1.4),
            (0.40, 0.99, 0.95, 12, 3),
            (0.55, 0.995, 0.98, 12, 3),
            (0.30, 0.98, 0.95, 14, 1.4),
            (0.65, 0.99, 0.97, 10, 3),
            (0.466, 0.999, 0.99, 12, 3),
            (0.466, 0.995, 0.98, 5, 0.928052),
        ]
    ):
        tasks.append(
            PaperTask(
                task_id=f"binary-{i:02d}",
                case="binary",
                feed_fraction=feed,
                purity=purity,
                recovery=recovery,
                max_stages=stages,
                max_reflux=reflux,
            )
        )
    for i, (purity, recovery, stages, reflux, margin) in enumerate(
        [
            (0.99, 0.97, 200, 56, 0.0005),
            (0.995, 0.98, 200, 56, 0.0005),
            (0.995, 0.98, 183, 48, 0.0001),
            (0.995, 0.98, 180, 48, 0.0005),
            (0.996, 0.981, 200, 56, 0.0005),
            (0.999, 0.985, 200, 56, 0.0005),
            (0.98, 0.96, 160, 40, 0.0005),
            (0.995, 0.98, 200, 40, 0.0005),
            (0.995, 0.98, 183, 48, 0.001),
            (0.9999, 0.99, 200, 56, 0.0005),
        ]
    ):
        tasks.append(
            PaperTask(
                task_id=f"extractive-{i:02d}",
                case="extractive",
                feed_fraction=0.5,
                purity=purity,
                recovery=recovery,
                max_stages=stages,
                max_reflux=reflux,
                margin=margin,
            )
        )
    for i, (temp, solvent, recovery, retention, stages) in enumerate(
        [
            (303.15, 1.5, 0.7, 0.8, 4),
            (303.15, 1.5, 0.7, 0.8, 2),
            (298.15, 1.5, 0.7, 0.8, 4),
            (303.15, 1.5, 0.65, 0.8, 4),
            (303.15, 1.5, 0.75, 0.8, 4),
            (303.15, 1.5, 0.7, 0.85, 4),
            (303.15, 1.2, 0.7, 0.8, 4),
            (303.15, 1.8, 0.7, 0.8, 4),
            (298.15, 1.5, 0.65, 0.85, 4),
            (303.15, 1.5, 0.9, 0.9, 4),
        ]
    ):
        tasks.append(
            PaperTask(
                task_id=f"extraction-{i:02d}",
                case="extraction",
                feed_fraction=4 / 15,
                temperature_K=temp,
                solvent_total=solvent,
                recovery=recovery,
                retention=retention,
                max_stages=stages,
            )
        )
    return tasks
