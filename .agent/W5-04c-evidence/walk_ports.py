"""W5-04c: run the unchanged W5-04 walkthrough with API ports 9001+ so it cannot collide with the parallel W5-04b builder."""
import sys
sys.path.insert(0, r"C:\Users\assef\Bineyame\AssetOpsV1-review6\tools")
import w504_ev_work_walkthrough as W  # noqa: E402
W.PORTS = {"positive": 9001, "zero": 9002, "worstcase": 9003, "unknown": 9005, "forbidden": 9006, "unavailable": 9007}
raise SystemExit(W.main(sys.argv[1:]))
