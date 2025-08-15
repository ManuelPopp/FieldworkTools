from html import parser
import os
import numpy as np
from warnings import warn

def validate_args(args):
    ## Ensure the output is a .kmz file
    if os.path.splitext(args.destfile)[1].lower() != ".kmz":
        args.destfile = args.destfile + ".kmz"

    ## Get altitude from sensor parameters and GSD if not set
    if args.altitude is None:
        args.altitude = args.gsd * args.sensorfactor

    ## Set plot width and height if missing
    if args.width is None and args.height is None:
        args.width = np.sqrt(args.area)
        args.height = np.sqrt(args.area)

    if args.width is None:
        args.width = args.area / args.height

    if args.height is None:
        args.height = args.area / args.width

    ## Set spacing if missing; else, overwrite side overlap
    if args.spacing is None:
        """Not working! Not working! Not working! Not working! Not working!
        args.spacing = np.tan(
            (args.horizontalfov / 2) * np.pi / 180
            ) * args.altitude * (2 - args.sideoverlap)
        """
        c1, c2 = args.coefficients
        args.spacing = (c1 * args.sideoverlap * 100 + c2) * args.altitude
    else:
        """Not working! Not working! Not working! Not working! Not working!
        args.sideoverlap = 2 - args.spacing / (
            np.tan((args.horizontalfov / 2) * np.pi / 180) * args.altitude
            )
        """
        c1, c2 = args.coefficients
        args.sideoverlap = (args.spacing / (args.altitude * 100) - c2) / c1
        warn(
            "Spacing set by user. This will override the side overlap. " +
            f"Side overlap is now {args.sideoverlap}."
            )

    if args.sideoverlap < 0 or args.sideoverlap > 1:
        raise ValueError(
            "Side overlap (fraction) must be between 0 and 1. " +
            f"Got {args.sideoverlap}."
            )

    ## Compute a default buffer value if not set
    if args.buffer is None:
        args.buffer = args.spacing / 2

    args.buffer = int(round(args.buffer))

    ## Use integers where possible (like DJI does)
    if args.altitude == int(args.altitude):
        args.altitude = int(args.altitude)

    if args.tosecurealt == int(args.tosecurealt):
        args.tosecurealt = int(args.tosecurealt)

    if args.flightspeed == int(args.flightspeed):
        args.flightspeed = int(args.flightspeed)

    if args.transitionspeed == int(args.transitionspeed):
        args.transitionspeed = int(args.transitionspeed)
    
    if args.altitudetype == "dsm" and not args.dsm_path:
        parser.error("--dsm_path is required when altitude type is 'dsm'")
    
    ## Print input settings
    print("== Settings ==")
    for arg, value in args.__dict__.items():
        print(f"{arg}={value}")
    
    return args