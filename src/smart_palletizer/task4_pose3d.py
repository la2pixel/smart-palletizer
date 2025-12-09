"""
Wrapper for 6D Pose Estimation
"""

from pathlib import Path
from .task4_6dpose_est import main as task4_main


def run_task4(data_root, verbose=True):
    """
    Parameters
    ----------
    data_root : str or Path
        Path to the dataset root. It should contain:
            medium_box/
            small_box/
        The underlying main() function uses these directories directly.
    verbose : bool, default=True
        If True, prints status messages during execution.
    """
    data_root = Path(data_root)

    if verbose:
        print("\n[Task 4] Starting 6D pose estimation")
        print("[Task 4] Dataset root:", data_root.resolve())

    # The estimator internally processes both medium_box and small_box and wrapper doesn't override this.
    task4_main()

    if verbose:
        print("[Task 4] Completed.\n")
