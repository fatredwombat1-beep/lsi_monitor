import sys, cv2, numpy as np, trimesh
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

def mask_from(path, width_mm, min_line_mm=0.9, up=3):
    g = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    g = cv2.resize(g, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    g = cv2.GaussianBlur(g, (3,3), 0)
    m = (g < 140).astype(np.uint8)
    mmpx = width_mm / g.shape[1]
    # thicken thin lines so every stroke is at least min_line_mm wide
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    r = max(0, int(round((min_line_mm/2) / mmpx - np.percentile(dt[dt>0], 75))))
    if r: m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1)))
    # drop specks < 0.6 mm^2
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA]*mmpx*mmpx > 0.6
    m = keep[lab].astype(np.uint8)
    # fill pinholes < 0.5 mm^2 inside lines
    inv = 1-m; n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    small = np.zeros(n, bool); small[1:] = st[1:, cv2.CC_STAT_AREA]*mmpx*mmpx < 0.5
    m[small[lab]] = 1
    return m, mmpx

def polys(m, mmpx):
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]; out = []
    for i, c in enumerate(cs):
        if hier[i][3] != -1: continue
        def pts(c): return cv2.approxPolyDP(c, 0.8, True)[:,0,:].astype(float)
        sh = pts(c)
        if len(sh) < 3: continue
        holes = []; j = hier[i][2]
        while j != -1:
            h = pts(cs[j])
            if len(h) >= 3: holes.append(h)
            j = hier[j][0]
        p = Polygon(sh, holes).buffer(0)
        if not p.is_empty: out.append(p)
    g = unary_union(out)
    g = affinity.scale(g, mmpx, -mmpx, origin=(0,0))  # px -> mm, flip y
    return g

def extrude(g, h, z0=0):
    geoms = g.geoms if hasattr(g,'geoms') else [g]
    ms = []
    for p in geoms:
        if p.area < 0.3: continue
        mm = trimesh.creation.extrude_polygon(p, h); mm.apply_translation([0,0,z0]); ms.append(mm)
    return trimesh.util.concatenate(ms)

def main(src, name, width_mm, outdir, base=1.6, relief=2.0, margin=0):
    m, mmpx = mask_from(src, width_mm)
    cv2.imwrite(f"{outdir}/{name}_preview.png", (1-m)*255)
    g = polys(m, mmpx)
    lines = extrude(g, base+relief)
    minx, miny, maxx, maxy = g.bounds
    plate = Polygon([(minx-margin,miny-margin),(maxx+margin,miny-margin),(maxx+margin,maxy+margin),(minx-margin,maxy+margin)])
    plate_m = extrude(plate, base)
    plaque = trimesh.boolean.union([plate_m, lines], engine='manifold', check_volume=False)
    lines_only = extrude(g, relief)
    for mesh in (plaque, lines_only):
        mesh.apply_translation(-mesh.bounds[0])
    plaque.export(f"{outdir}/{name}_plaque.stl"); lines_only.export(f"{outdir}/{name}_lines_only.stl")
    print(name, "plaque", plaque.extents.round(1), "watertight", plaque.is_watertight, "tris", len(plaque.faces))
    print(name, "lines_only", lines_only.extents.round(1), "parts", len(g.geoms) if hasattr(g,'geoms') else 1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4], margin=float(sys.argv[5]))
