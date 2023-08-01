import argparse
import asyncio
from dataclasses import asdict

import aiohttp
import json

from raw_suppliers import RequestCourseSupplier, MaslulPageSupplier, MaslulAllPageSupplier
from magics import *


async def test():
    s = RequestCourseSupplier("67562", 2024)
    course = await s.supply()
    print(json.dumps(asdict(course), indent=2, ensure_ascii=False))


async def test_maslul():
    connector = aiohttp.TCPConnector(force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        s = MaslulAllPageSupplier(2024, '12', '0532', '3080', session=session)
        courses = await s.supply()
        print(f"Normal: {len(courses)}, Dedup: {len(set(courses))}")
        # print(json.dumps([asdict(course) for course in courses], indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', type=int, required=True)
    courses = parser.add_mutually_exclusive_group(required=True)
    courses.add_argument('-c', '--courses', nargs='+')
    courses.add_argument('-m', '--maslul', type=int)
    parser.add_argument('--faculty', type=int)
    parser.add_argument('--hug', type=str)
    parser.add_argument('-t', '--toar', type=Toar, choices=list(Toar), default=Toar.Any,
                        help="The type of degree (boger,...). "
                             "Default is all degrees.")
    parser.add_argument('-s', '--shana', default=ToarYear.Any, help="Year of the maslul to download. "
                                                                    "If not specified will download all.")
    parser.add_argument('-p', '--page', type=int, help="Page to download in the maslul. "
                                                       "If not specified will be all pages.")
    parser.add_argument('-o', '--output', required=False, help="Output file for the scraped courses. "
                                                               "If not specified will be printed to stdout.")
    # parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.maslul and (args.faculty is None or args.hug is None):
        parser.error("If --maslul is specified, --faculty and --hug need to be specified as well.")



if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
