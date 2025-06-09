import os
import uuid
import ezdxf
import json
import traceback

TMP_DIR = "/tmp"

def safe_tuple_float(lst):
    try:
        return tuple(map(float, lst))
    except Exception as e:
        print(f"[safe_tuple_float] Error al convertir: {lst} - {e}")
        return tuple(lst)

def generar_dxf_desde_instrucciones(data: dict) -> str:
    filename = f"{uuid.uuid4().hex}.dxf"
    filepath = os.path.join(TMP_DIR, filename)

    print(f"[DXF] Guardando en: {filepath}")
    doc = ezdxf.new(dxfversion="R2010")
    doc.header['$INSUNITS'] = 4
    msp = doc.modelspace()

    for capa in data.get("capas", []):
        print(f"[Capa] {capa}")
        doc.layers.new(name=capa["nombre"], dxfattribs={"color": capa.get("color", 7)})

    for bloque in data.get("bloques", []):
        try:
            print(f"[Bloque] {bloque['nombre']}")
            b = doc.blocks.new(name=bloque["nombre"])
            for entidad in bloque.get("entidades", []):
                tipo = entidad["tipo"]
                print(f"  [Entidad bloque] Tipo: {tipo}")
                if tipo == "rectangulo":
                    b.add_lwpolyline([safe_tuple_float(pt) for pt in entidad["puntos"]], close=True)
                elif tipo == "circulo":
                    b.add_circle(center=safe_tuple_float(entidad["centro"]), radius=float(entidad["radio"]))
                elif tipo == "texto":
                    txt = b.add_text(entidad["texto"], dxfattribs={"height": float(entidad.get("alto", 250))})
                    txt.set_pos(safe_tuple_float(entidad["posicion"]))
                    txt.set_align("LEFT")
        except Exception as e:
            print(f"   Error en bloque: {bloque.get('nombre', '')} - {e}")

    for figura in data.get("figuras", []):
        try:
            tipo = figura.get("tipo")
            capa = figura.get("capa", "default")
            color = int(figura.get("color", 7))
            dxf_attribs = {"layer": capa, "color": color}
            print(f"[Figura] Tipo: {tipo}")

            if tipo == "rectangulo":
                puntos = [safe_tuple_float(pt) for pt in figura["puntos"]]
                msp.add_lwpolyline(puntos, close=True, dxfattribs=dxf_attribs)

            elif tipo == "linea":
                msp.add_line(safe_tuple_float(figura["inicio"]), safe_tuple_float(figura["fin"]), dxfattribs=dxf_attribs)

            elif tipo == "circulo":
                msp.add_circle(safe_tuple_float(figura["centro"]), float(figura["radio"]), dxfattribs=dxf_attribs)

            elif tipo == "texto":
                texto = msp.add_text(
                    figura["texto"],
                    dxfattribs={"height": float(figura.get("alto", 250)), "color": color}
                )
                texto.set_pos(safe_tuple_float(figura["posicion"]))
                texto.set_align("LEFT")

            elif tipo == "arco":
                msp.add_arc(
                    center=safe_tuple_float(figura["centro"]),
                    radius=float(figura["radio"]),
                    start_angle=float(figura["inicio"]),
                    end_angle=float(figura["fin"]),
                    dxfattribs=dxf_attribs
                )

            elif tipo == "elipse":
                msp.add_ellipse(
                    center=safe_tuple_float(figura["centro"]),
                    major_axis=safe_tuple_float(figura["eje_mayor"]),
                    ratio=float(figura.get("relacion", 0.5)),
                    dxfattribs=dxf_attribs
                )

            elif tipo == "hatch":
                puntos = [safe_tuple_float(pt) for pt in figura["puntos"]]
                hatch = msp.add_hatch(color=color, dxfattribs={"layer": capa})
                hatch.paths.add_polyline_path(puntos, is_closed=True)
                hatch.set_solid_fill()

            elif tipo == "cota":
                msp.add_linear_dim(
                    base=safe_tuple_float(figura["base"]),
                    p1=safe_tuple_float(figura["inicio"]),
                    p2=safe_tuple_float(figura["fin"]),
                    angle=float(figura.get("angulo", 0)),
                    override={"dimtxt": figura.get("texto", "")}
                ).render()

            elif tipo == "bloque":
                if "nombre" in figura and "insertar_en" in figura:
                    msp.add_blockref(
                        figura["nombre"],
                        safe_tuple_float(figura["insertar_en"]),
                        dxfattribs=dxf_attribs
                    )

            elif tipo == "polilinea3d":
                puntos = [safe_tuple_float(pt) for pt in figura["puntos"]]
                msp.add_polyline3d(puntos, dxfattribs=dxf_attribs)

        except Exception as e:
            print(f" Error procesando figura: {figura} - {e}")
            traceback.print_exc()

    layout = doc.layout()
    layout.add_line((0, 0), (210, 0), dxfattribs={"color": 6})
    layout.add_text("Plano generado", dxfattribs={"height": 10}).set_pos((10, 20))

    doc.saveas(filepath)
    return filepath

def main(context):
    req = context.req
    res = context.res

    try:
        body = json.loads(req.body_raw)
        print(f"[Solicitud recibida] Body: {json.dumps(body, indent=2)}")

        if not body or "capas" not in body or "figuras" not in body:
            return res.json({"error": "Debes enviar un JSON válido con 'capas' y 'figuras'."}, 400)

        dxf_path = generar_dxf_desde_instrucciones(body)

        with open(dxf_path, "rb") as f:
            return res.send(f.read(), 200, {
                "Content-Type": "application/dxf",
                "Content-Disposition": f'attachment; filename="{os.path.basename(dxf_path)}"'
            })

    except Exception as e:
        print(f" Error general: {e}")
        traceback.print_exc()
        return res.json({"error": str(e)}, 500)
