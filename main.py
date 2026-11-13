import glob, json, math, os

def _poly(c, x):
    v = 0.0
    for a in c:
        v = v * x + a
    return v


# Inverse standard normal CDF (Acklam), accurate to ~1e-9.
def _ppf(p):
    a = (-39.69683028665376, 220.9460984245205, -275.9285104469687,
         138.3577518672690, -30.66479806614716, 2.506628277459239)
    b = (-54.47609879822406, 161.5858368580409, -155.6989798598866,
         66.80131188771972, -13.28068155288572)
    c = (-0.007784894002430293, -0.3223964580411365, -2.400758277161838,
         -2.549732539343734, 4.374664141464968, 2.938163982698783)
    d = (0.007784695709041462, 0.3224671290700398, 2.445134137142996,
         3.754408661907416)
    if p < 0.02425:
        q = math.sqrt(-2.0 * math.log(p))
        return _poly(c, q) / (_poly(d, q) * q + 1.0)
    if p <= 0.97575:
        q = p - 0.5
        r = q * q
        return _poly(a, r) * q / (_poly(b, r) * r + 1.0)
    q = math.sqrt(-2.0 * math.log(1.0 - p))
    return -_poly(c, q) / (_poly(d, q) * q + 1.0)


def _c6(x):
    v = round(min(1.0, max(0.0, x)) * 1000000.0) / 1000000.0
    return v + 0.0


def _sigma(prices):
    n = len(prices)
    w = 360 if n - 1 > 360 else n - 1
    if w < 10:
        return 0.0025
    s = 0.0
    for i in range(n - w - 1, n - 1):
        d = abs(prices[i + 1] - prices[i])
        s += d if d < 0.05 else 0.05
    v = s / w / 0.7978845608028654
    return 0.0003 if v < 0.0003 else (0.02 if v > 0.02 else v)


def _forecast(prices, horizon, zs):
    x = prices[-1] if prices else 0.5
    sg = _sigma(prices) if prices else 0.0025
    rows = []
    for h in range(1, horizon + 1):
        s = sg * math.sqrt(h)
        rows.append([_c6(x + z * s) for z in zs])
    return rows


def main():
    inp = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(inp, "*.in"))):
        cid = os.path.basename(path)[:-3]
        with open(path) as f:
            case = json.load(f)
        horizon = case.get("horizon_minutes", 240)
        taus = case.get("quantiles", [0.05, 0.25, 0.5, 0.75, 0.95])
        zs = [_ppf(t) for t in taus]
        fc = [{"id": m["id"], "q": _forecast(m["prices"], horizon, zs)}
              for m in case["markets"]]
        with open(os.path.join(out, cid + ".out"), "w") as f:
            f.write(json.dumps({"forecasts": fc}, separators=(",", ":")) + "\n")


main()
