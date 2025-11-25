"""
pricing.py
~~~~~~~~~~~

This module exposes a single function ``calculer_prix_total`` used by the
Streamlit application to estimate the selling price (hors taxes) of a
made‑to‑measure Moroccan sofa (canapé marocain).  It works by invoking
the rendering code contained in the companion Matplotlib/Turtle script
(`canapefullv88_matplot.py`) to derive the geometry of the sofa.  The
rendering functions in that script print a console report describing the
sofa: number of banquettes, number of angle banquettes, backrests
(dossiers), armrests (accoudoirs) and, crucially, the dimensions of
each foam cushion.  These values are then combined with a handful of
form‑derived parameters (foam density, thickness, decorative cushions,
traversins, surmatelas and arrondis) to arrive at a price.

The pricing logic follows the rules provided by the user:

* **Foam price** – for each cushion (whether straight or angle) the
  price is computed as::

      (longueur * largeur * epaisseur * densite * 16) / 1_000_000

  where ``longueur`` and ``largeur`` are the dimensions printed in the
  console report, ``epaisseur`` is the thickness entered by the user
  (in centimetres) and ``densite`` is derived from the selected foam
  type (D25 → 25, D30 → 30, HR35 → 35, HR45 → 45).

* **Fabric price** – for each cushion the fabric consumption depends
  upon its width and the thickness.  If ``largeur * epaisseur * 2 > 140``
  the price is ``(longueur/100) * 105``; otherwise it is
  ``(longueur/100) * 74``.  This heuristic mirrors the way wider
  cushions require more expensive fabric per metre.

* **Support price** – straight banquettes have a base price of 225 €,
  angle banquettes 250 €, and backrests (dossiers) 250 € each.  These
  prices reflect the structure/support underneath the cushions.

* **Cushions** – decorative seat cushions (65 cm, 80 cm or 90 cm) and
  valise cushions are priced at 35 €, 44 €, 48 € and 70 € respectively.
  The counts for each category are read from the console report.  In
  addition, the user can specify extra decorative cushions via
  ``nb_coussins_deco`` which are charged at 15 € each.

* **Traversins** – each traversin (bolster cushion) costs 30 €.  The
  console report lists the base number of traversins; the user can add
  further traversins through ``nb_traversins_supp``.

* **Surmatelas** – a sur‑matelas (topper) adds 80 € per unit.  The
  Streamlit form exposes this as a boolean, so we treat it as either
  zero or one.

* **Arrondis** – rounded corners on banquettes incur an extra 20 € per
  banquette or angle.  The Streamlit app handles this surcharge
  externally; therefore ``calculer_prix_total`` does not include
  arrondis and leaves that responsibility to the caller.

The function returns a dictionary with the following keys:

``prix_ht``       – the calculated total price before tax,
``cout_revient_ht`` – a naïve estimate of the cost of goods sold (here
                      taken as 70 % of the selling price),
``tva``           – 20 % VAT applied to ``prix_ht``,
``total_ttc``     – the total price including VAT.

If the geometry cannot be computed (for example because the
configuration is invalid) the function will raise a RuntimeError with
the underlying exception.  Consumers should handle this and surface
meaningful error messages to end users.
"""

from __future__ import annotations

import contextlib
import importlib.machinery
import io
import os
import re
from typing import Dict, List, Tuple


def _load_canape_module() -> object:
    """Load and return the Matplotlib/Turtle based rendering module.

    The file provided by the user has a complex Unicode name.  To
    import it reliably we use ``importlib.machinery.SourceFileLoader``.
    Once loaded we monkey‑patch ``plt.show`` and ``turtle.done`` to
    no‑operations so that rendering does not block execution.  The
    resulting module is cached on first import.
    """
    global _CANAPE_MOD
    if '_CANAPE_MOD' in globals() and _CANAPE_MOD is not None:
        return _CANAPE_MOD
    # Determine the path relative to this file
    this_dir = os.path.dirname(os.path.abspath(__file__))
    # Hard‑coded filename as uploaded by the user; if it ever changes
    # update this string accordingly.
    # The rendering module used by the application is named
    # ``canapematplot.py``.  Update the filename accordingly so that
    # this pricing module can locate and import it.  If you need to
    # support other names in the future, consider adding a list of
    # candidates here.
    filename = 'canapematplot.py'
    path = os.path.join(this_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cannot find the canape rendering module at {path!r}")
    loader = importlib.machinery.SourceFileLoader('canape_render', path)
    mod = loader.load_module()
    # Patch out the blocking graphics calls
    try:
        import matplotlib
        # Use a non‑interactive backend if not already set
        matplotlib.use('Agg', force=True)
    except Exception:
        pass
    # Prevent the figure from appearing
    try:
        mod.plt.show = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    except Exception:
        pass
    # Suppress turtle.done (which calls plt.show internally)
    try:
        mod.turtle.done = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    except Exception:
        pass
    globals()['_CANAPE_MOD'] = mod
    return mod


def _call_render_function(mod: object, *, type_canape: str, tx: float | int | None, ty: float | int | None,
                          tz: float | int | None, profondeur: float | int | None, dossier_left: bool, dossier_bas: bool,
                          dossier_right: bool, acc_left: bool, acc_bas: bool, acc_right: bool,
                          meridienne_side: str | None, meridienne_len: float | int | None,
                          coussins: str | int | None) -> str:
    """Invoke the appropriate render function from the loaded module and capture its stdout.

    Parameters mirror those passed from the Streamlit form.  The choice
    of render function is based upon ``type_canape``.  When the function
    writes to stdout, its output is captured and returned.  If the
    underlying renderer raises an exception, it is propagated as a
    RuntimeError so that callers can report an error to the user.
    """
    # Determine which render function to call and arguments mapping
    try:
        render_func: callable
        kwargs: Dict[str, object] = {}
        t = (type_canape or '').lower()
        if 'simple' in t:
            # Simple sofa: only one banquette; only bottom dossier/accoudoirs matter
            render_func = getattr(mod, 'render_Simple1')
            kwargs = dict(
                tx=tx,
                profondeur=profondeur,
                dossier=dossier_bas,
                acc_left=acc_left,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len or 0,
                coussins=coussins or 'auto',
                window_title="simple"
            )
        elif 'l - sans angle' in t:
            render_func = getattr(mod, 'render_LNF')
            kwargs = dict(
                tx=tx,
                ty=ty,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len or 0,
                coussins=coussins or 'auto',
                variant="auto",
                window_title="LNF"
            )
        elif 'l - avec angle' in t:
            render_func = getattr(mod, 'render_LF_variant')
            kwargs = dict(
                tx=tx,
                ty=ty,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                acc_left=acc_left,
                acc_bas=acc_bas,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len or 0,
                coussins=coussins or 'auto',
                window_title="LF"
            )
        elif 'u - sans angle' in t or (('u ' in t) and ('sans angle' in t)):
            render_func = getattr(mod, 'render_U')
            kwargs = dict(
                tx=tx,
                ty_left=ty,
                tz_right=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_bas=acc_bas,
                acc_right=acc_right,
                coussins=coussins or 'auto',
                variant="auto",
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len or 0,
                window_title="U"
            )
        elif 'u - 1' in t and 'angle' in t:
            # U with one angle – the first variant (others exist but are seldom used)
            render_func = getattr(mod, 'render_U1F_v1')
            kwargs = dict(
                tx=tx,
                ty=ty,
                tz=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len or 0,
                coussins=coussins or 'auto',
                window_title="U1F"
            )
        elif 'u - 2' in t and 'angle' in t:
            render_func = getattr(mod, 'render_U2f_variant')
            kwargs = dict(
                tx=tx,
                ty_left=ty,
                tz_right=tz,
                profondeur=profondeur,
                dossier_left=dossier_left,
                dossier_bas=dossier_bas,
                dossier_right=dossier_right,
                acc_left=acc_left,
                acc_bas=acc_bas,
                acc_right=acc_right,
                meridienne_side=meridienne_side,
                meridienne_len=meridienne_len or 0,
                coussins=coussins or 'auto',
                window_title="U2f"
            )
        else:
            raise ValueError(f"Unrecognised type_canape: {type_canape}")
        # Capture stdout while invoking the render function
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render_func(**kwargs)  # type: ignore[func-returns-value]
        return buf.getvalue()
    except Exception as exc:
        # Re‑wrap any exception to surface a helpful error upstream
        raise RuntimeError(f"Erreur lors de l'exécution du rendu: {exc}") from exc


def _parse_console_report(report: str) -> Dict[str, object]:
    """Parse the console report emitted by the rendering code.

    The report contains human‑readable lines describing the sofa.  This
    parser extracts numeric values and cushion dimensions from those
    lines.  Fields that do not appear in the report default to sensible
    values (e.g., 0 or empty lists).
    """
    # Initialise defaults
    result: Dict[str, object] = {
        'nb_banquettes': 0,
        'nb_banquettes_angle': 0,
        'nb_dossiers': 0,
        'nb_accoudoirs': 0,
        'dims_mousses': [],        # type: List[Tuple[float, float]]
        'dims_mousses_angle': [],  # type: List[Tuple[float, float]]
        'nb_coussins_65': 0,
        'nb_coussins_80': 0,
        'nb_coussins_90': 0,
        'nb_coussins_valise': 0,
        'nb_traversins': 0,
    }
    # Normalise quotes/apostrophes for consistency
    lines = [line.strip() for line in report.splitlines() if line.strip()]
    # Regex patterns
    pat_int = re.compile(r"\d+")
    pat_mousse = re.compile(r"^Dimension mousse\s+(\d+)\s*:\s*([0-9]+)\s*,\s*([0-9]+)")
    pat_mousse_angle = re.compile(r"^Dimension mousse angle\s+(\d+)\s*:\s*([0-9]+)\s*,\s*([0-9]+)")
    for line in lines:
        # Number of banquettes
        if line.lower().startswith('nombre de banquettes'):
            m = pat_int.search(line)
            if m:
                result['nb_banquettes'] = int(m.group())
        elif 'banquette d’angle' in line.lower() or 'banquette d\'angle' in line.lower():
            m = pat_int.search(line)
            if m:
                result['nb_banquettes_angle'] = int(m.group())
        elif line.lower().startswith('nombre de dossiers'):
            m = pat_int.search(line)
            if m:
                result['nb_dossiers'] = int(m.group())
        elif line.lower().startswith('nombre d’accoudoir') or line.lower().startswith("nombre d'accoudoir"):
            m = pat_int.search(line)
            if m:
                result['nb_accoudoirs'] = int(m.group())
        elif line.lower().startswith('dimension mousse angle'):
            m = pat_mousse_angle.match(line)
            if m:
                L = float(m.group(2)); P = float(m.group(3))
                result['dims_mousses_angle'].append((L, P))
        elif line.lower().startswith('dimension mousse'):
            m = pat_mousse.match(line)
            if m:
                L = float(m.group(2)); P = float(m.group(3))
                result['dims_mousses'].append((L, P))
        elif 'nombre de coussins 65' in line.lower():
            # Extract the quantity after the colon; avoid capturing the size (65)
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    qty = int(re.findall(r"\d+", parts[1])[0])
                    result['nb_coussins_65'] = qty
                except Exception:
                    pass
        elif 'nombre de coussins 80' in line.lower():
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    qty = int(re.findall(r"\d+", parts[1])[0])
                    result['nb_coussins_80'] = qty
                except Exception:
                    pass
        elif 'nombre de coussins 90' in line.lower():
            parts = line.split(':')
            if len(parts) >= 2:
                try:
                    qty = int(re.findall(r"\d+", parts[1])[0])
                    result['nb_coussins_90'] = qty
                except Exception:
                    pass
        elif 'nombre de coussins valises' in line.lower():
            m = pat_int.search(line)
            if m:
                result['nb_coussins_valise'] = int(m.group())
        elif 'nombre de traversin' in line.lower():
            m = pat_int.search(line)
            if m:
                result['nb_traversins'] = int(m.group())
        else:
            continue
    return result


def _density_from_type(type_mousse: str) -> float:
    """Map a foam type string to its numeric density.

    Supported values are D25, D30, HR35 and HR45.  The function is
    case‑insensitive and strips whitespace.  Unknown values fall back to
    a density of 25.
    """
    if not type_mousse:
        return 25.0
    t = str(type_mousse).strip().lower()
    if 'hr' in t:
        # high resilience foams are indicated by HRxx
        try:
            return float(t.replace('hr', '').replace(' ', ''))
        except Exception:
            return 35.0
    try:
        return float(t.replace('d', '').replace(' ', ''))
    except Exception:
        return 25.0


def _compute_foam_and_fabric_price(dims: List[Tuple[float, float]], thickness: float, density: float) -> Tuple[float, float]:
    """Compute the total foam and fabric prices for a list of cushions.

    The foam price uses the formula described in the module docstring.
    The fabric price applies the width*thickness*2 > 140 rule for each
    cushion.  Returns a tuple ``(foam_total, fabric_total)``.
    """
    foam_total = 0.0
    fabric_total = 0.0
    for L, W in dims:
        # Foam price
        foam_total += (L * W * thickness * density * 16.0) / 1_000_000.0
        # Fabric price
        if (W * thickness * 2.0) > 140.0:
            fabric_total += (L / 100.0) * 105.0
        else:
            fabric_total += (L / 100.0) * 74.0
    return foam_total, fabric_total


def calculer_prix_total(
    *,
    type_canape: str,
    tx: float | int | None = None,
    ty: float | int | None = None,
    tz: float | int | None = None,
    profondeur: float | int | None = None,
    type_coussins: str | int | None = None,
    type_mousse: str | None = None,
    epaisseur: float | int | None = None,
    acc_left: bool = False,
    acc_right: bool = False,
    acc_bas: bool = False,
    dossier_left: bool = False,
    dossier_bas: bool = False,
    dossier_right: bool = False,
    nb_coussins_deco: int = 0,
    nb_traversins_supp: int = 0,
    has_surmatelas: bool | int = False,
    has_meridienne: bool | None = None,
    meridienne_side: str | None = None,
    meridienne_len: float | int | None = None
) -> Dict[str, float]:
    """Calculate the total price for the configured sofa.

    This function orchestrates the loading of the rendering module, calls
    the appropriate render function based on ``type_canape``, parses the
    resulting console report and then applies the pricing rules.  The
    return value is a dictionary with keys ``prix_ht``, ``cout_revient_ht``,
    ``tva`` and ``total_ttc``.  It does not include arrondis; callers
    should add the 20 € per banquette/angle surcharge separately if
    applicable.
    """
    # Normalise numeric parameters and set sensible defaults
    tx = float(tx or 0)
    ty = float(ty or 0)
    tz = float(tz or 0)
    profondeur = float(profondeur or 0)
    epaisseur_val = float(epaisseur or 0)
    density = _density_from_type(type_mousse or 'D25')

    # Load rendering module and capture console output
    mod = _load_canape_module()
    try:
        report = _call_render_function(
            mod,
            type_canape=type_canape,
            tx=tx,
            ty=ty,
            tz=tz,
            profondeur=profondeur,
            dossier_left=dossier_left,
            dossier_bas=dossier_bas,
            dossier_right=dossier_right,
            acc_left=acc_left,
            acc_bas=acc_bas,
            acc_right=acc_right,
            meridienne_side=meridienne_side,
            meridienne_len=meridienne_len or 0,
            coussins=type_coussins or 'auto'
        )
    except Exception as exc:
        # Propagate errors; in a Streamlit app the caller will handle them
        raise
    # Parse the report
    data = _parse_console_report(report)
    # Compute foam and fabric prices for straight cushions and angle cushions
    dims = list(data.get('dims_mousses', []))
    dims_angle = list(data.get('dims_mousses_angle', []))
    foam_straight, fabric_straight = _compute_foam_and_fabric_price(dims, epaisseur_val, density)
    foam_angle, fabric_angle = _compute_foam_and_fabric_price(dims_angle, epaisseur_val, density)
    foam_total = foam_straight + foam_angle
    fabric_total = fabric_straight + fabric_angle
    # Support prices
    nb_banquettes = int(data.get('nb_banquettes') or 0)
    nb_banquettes_angle = int(data.get('nb_banquettes_angle') or 0)
    nb_dossiers = int(data.get('nb_dossiers') or 0)
    support_total = 0.0
    support_total += nb_banquettes * 225.0
    support_total += nb_banquettes_angle * 250.0
    support_total += nb_dossiers * 250.0
    # Decorative pillows and valises
    nb_coussins_65 = int(data.get('nb_coussins_65') or 0)
    nb_coussins_80 = int(data.get('nb_coussins_80') or 0)
    nb_coussins_90 = int(data.get('nb_coussins_90') or 0)
    nb_coussins_valise = int(data.get('nb_coussins_valise') or 0)
    cushion_total = (
        nb_coussins_65 * 35.0
        + nb_coussins_80 * 44.0
        + nb_coussins_90 * 48.0
        + nb_coussins_valise * 70.0
        + nb_coussins_deco * 15.0
    )
    # Traversins
    nb_traversins = int(data.get('nb_traversins') or 0) + int(nb_traversins_supp or 0)
    traversin_total = nb_traversins * 30.0
    # Surmatelas
    nb_surmatelas = 1 if has_surmatelas else 0
    surmatelas_total = nb_surmatelas * 80.0
    # Armrests: there is no explicit price provided in the specification.
    # They are implicit in the support price; therefore we do not add
    # anything here.  Should a future version require armrest pricing,
    # adjust accordingly.
    # Sum all components to obtain the HT price
    prix_ht = foam_total + fabric_total + support_total + cushion_total + traversin_total + surmatelas_total
    # Compute a rudimentary cost of goods: assume 70 % of selling price
    cout_revient_ht = prix_ht * 0.70
    # VAT at 20 %
    tva = round(prix_ht * 0.20, 2)
    total_ttc = round(prix_ht + tva, 2)
    # Round HT prices to two decimals as well for consistency
    prix_ht = round(prix_ht, 2)
    cout_revient_ht = round(cout_revient_ht, 2)
    return {
        'prix_ht': prix_ht,
        'cout_revient_ht': cout_revient_ht,
        'tva': tva,
        'total_ttc': total_ttc
    }
