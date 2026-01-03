import argparse
from nych.lexicon import LEXICON
from nych.visualizer import NychVisualizer


def cmd_inspect(args):
    print("NYCH INSPECT")
    print("============")
    for glyph, sym in LEXICON.items():
        print(
            f"{glyph} | meaning={sym.meaning} | address={sym.address}"
        )


def cmd_visualize(args):
    viz = NychVisualizer()
    viz.plot_symbols(list(LEXICON.values()))

    if args.save:
        viz.save(args.save)
        print(f"saved visualization to {args.save}")

    if args.show or not args.save:
        viz.show()


def main():
    parser = argparse.ArgumentParser(prog="nych")
    sub = parser.add_subparsers(dest="command")

    inspect_p = sub.add_parser("inspect", help="inspect NYCH symbols")
    inspect_p.set_defaults(func=cmd_inspect)

    vis_p = sub.add_parser("visualize", help="visualize NYCH locality")
    vis_p.add_argument("--save", type=str, default=None)
    vis_p.add_argument("--show", action="store_true")
    vis_p.set_defaults(func=cmd_visualize)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)
