import argparse
import json
from nych.competency import analyze_utterance
from nych.lexicon import LEXICON
from nych.semantic_encoding import audit_summary, encode_text
from nych.state_roles import tag_roles
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


def _sense_bindings(values):
    result = {}
    for value in values or []:
        try:
            position, sense_id = value.split("=", 1)
            result[int(position)] = sense_id
        except (ValueError, TypeError) as exc:
            raise SystemExit(f"invalid --sense {value!r}; expected POSITION=SENSE_ID") from exc
    return result


def cmd_encode(args):
    encoded, records = encode_text(
        args.text,
        sense_choices=_sense_bindings(args.sense),
        registry_path=args.registry,
        enable_spans=not args.no_spans,
    )
    payload = {"original": args.text, "encoded": encoded, "records": records,
               "audit": audit_summary(records)}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else encoded)


def cmd_analyze(args):
    result = analyze_utterance(args.text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_parse(args):
    print(json.dumps(tag_roles(args.text), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(prog="nych")
    sub = parser.add_subparsers(dest="command")

    inspect_p = sub.add_parser("inspect", help="inspect NYCH symbols")
    inspect_p.set_defaults(func=cmd_inspect)

    vis_p = sub.add_parser("visualize", help="visualize NYCH locality")
    vis_p.add_argument("--save", type=str, default=None)
    vis_p.add_argument("--show", action="store_true")
    vis_p.set_defaults(func=cmd_visualize)

    encode_p = sub.add_parser("encode", help="sense-first semantic encoding")
    encode_p.add_argument("text")
    encode_p.add_argument("--sense", action="append", default=[],
                          help="explicit zero-based POSITION=SENSE_ID binding")
    encode_p.add_argument("--registry", default=None, help="alternate registry JSON")
    encode_p.add_argument("--no-spans", action="store_true", help="disable multiword Gestalts")
    encode_p.add_argument("--json", action="store_true", help="include records and audit")
    encode_p.set_defaults(func=cmd_encode)

    analyze_p = sub.add_parser(
        "analyze", help="vernacular-based modality/domain classification + competency score"
    )
    analyze_p.add_argument("text")
    analyze_p.set_defaults(func=cmd_analyze)

    parse_p = sub.add_parser(
        "parse", help="pre-Gestalt state-role tagging (action/enumerator/object/tense/state)"
    )
    parse_p.add_argument("text")
    parse_p.set_defaults(func=cmd_parse)

    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
