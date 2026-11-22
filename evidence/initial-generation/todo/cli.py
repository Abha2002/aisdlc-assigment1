"""Command-line interface for the todo package."""

import argparse
import json
import sys

from todo.errors import TodoError, ValidationError
from todo.service import TaskService


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValidationError(message)


def _int_id(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValidationError("task id must be an integer") from exc
    return parsed


def _build_parser():
    parser = _ArgumentParser(prog="todo")
    parser.add_argument("--file", default="tasks.json")
    commands = parser.add_subparsers(dest="command", required=True)

    add_parser = commands.add_parser("add")
    add_parser.add_argument("title")
    add_parser.add_argument("--priority", default="medium")
    add_parser.add_argument("--tag", action="append", default=None)

    get_parser = commands.add_parser("get")
    get_parser.add_argument("id", type=_int_id)

    edit_parser = commands.add_parser("edit")
    edit_parser.add_argument("id", type=_int_id)
    edit_parser.add_argument("--title", default=None)
    edit_parser.add_argument("--priority", default=None)
    edit_parser.add_argument("--tag", action="append", default=None)

    delete_parser = commands.add_parser("delete")
    delete_parser.add_argument("id", type=_int_id)

    status_parser = commands.add_parser("status")
    status_parser.add_argument("id", type=_int_id)
    status_parser.add_argument("new_status")

    list_parser = commands.add_parser("list")
    list_parser.add_argument("--tag", default=None)
    list_parser.add_argument("--status", default=None)
    list_parser.add_argument("--sort", choices=("priority", "id"), default="priority")
    return parser


def _dispatch(args, service):
    if args.command == "add":
        return service.add_task(args.title, args.priority, args.tag)
    if args.command == "get":
        return service.get_task(args.id)
    if args.command == "edit":
        return service.update_task(
            args.id,
            title=args.title,
            priority=args.priority,
            tags=args.tag,
        )
    if args.command == "delete":
        result = service.delete_task(args.id)
        return {"deleted": args.id} if result is None else result
    if args.command == "status":
        return service.set_status(args.id, args.new_status)
    return service.list_tasks(tag=args.tag, status=args.status, sort=args.sort)


def main(argv=None):
    parser = _build_parser()
    try:
        args = parser.parse_args(sys.argv[1:] if argv is None else argv)
        result = _dispatch(args, TaskService(args.file))
    except TodoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0
