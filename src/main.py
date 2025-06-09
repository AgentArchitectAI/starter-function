import os
import uuid
import ezdxf
import json
from flask import Flask, request, send_file, Response
from ezdxf.addons.drawing import matplotlib

app = Flask(__name__)
os.makedirs("tmp", exist_ok=True)


def generar_dxf_desde_instrucciones(data: dict) -> str:
    filename = f"{uuid.uuid4().hex}.dxf"
    filepath = os.path.join("tmp", filename)

    doc = ezdxf.new(dxfversion="R2010")
    doc.header['$INSUNITS'] = 4  

    msp = doc.modelspace()

    for capa in data.get("capas", []):
        doc.layers.new(name=capa["nombre"], dxfattribs={"color": capa.get("color", 7)})

    for bloque in data.get("bloques", []):
        try:
            b = doc.blocks.new(name=bloque["nombre"])
            for entidad in bloque.get("entidades", []):
                tipo = entidad["tipo"]
                if tipo == "rectangulo":
                    b.add_lwpolyline(entidad["puntos"], close=True)
                elif tipo == "circulo":
                    b.add_circle(center=entidad["centro"], radius=entidad["radio"])
        except Exception:
            continue  

    for figura in data.get("figuras", []):
        tipo = figura.get("tipo")
        capa = figura.get("capa", "default")
        color = figura.get("color", 7)
        dxf_attribs = {"layer": capa, "color": color}

        if tipo == "rectangulo":
            puntos = figura["puntos"]
            msp.add_lwpolyline(puntos, close=True, dxfattribs=dxf_attribs)

        elif tipo == "linea":
            msp.add_line(tuple(figura["inicio"]), tuple(figura["fin"]), dxfattribs=dxf_attribs)

        elif tipo == "circulo":
            msp.add_circle(tuple(figura["centro"]), figura["radio"], dxfattribs=dxf_attribs)

        elif tipo == "texto":
            msp.add_text(
                figura["texto"],
                dxfattribs={"height": figura.get("alto", 250), "color": color}
            ).set_pos(tuple(figura["posicion"]))

        elif tipo == "arco":
            msp.add_arc(
                center=tuple(figura["centro"]),
                radius=figura["radio"],
                start_angle=figura["inicio"],
                end_angle=figura["fin"],
                dxfattribs=dxf_attribs
            )

        elif tipo == "elipse":
            msp.add_ellipse(
                center=tuple(figura["centro"]),
                major_axis=tuple(figura["eje_mayor"]),
                ratio=figura.get("relacion", 0.5),
                dxfattribs=dxf_attribs
            )

        elif tipo == "hatch":
            hatch = msp.add_hatch(color=color, dxfattribs={"layer": capa})
            path = hatch.paths.add_polyline_path(figura["puntos"], is_closed=True)
            hatch.set_solid_fill()

        elif tipo == "cota":
            msp.add_linear_dim(
                base=tuple(figura["base"]),
                p1=tuple(figura["inicio"]),
                p2=tuple(figura["fin"]),
                angle=figura.get("angulo", 0),
                override={"dimtxt": figura.get("texto", "")}
            ).render()

        elif tipo == "bloque":
            if "nombre" not in figura or "insertar_en" not in figura:
                continue
            try:
                msp.add_blockref(figura["nombre"], tuple(figura["insertar_en"]), dxfattribs=dxf_attribs)
            except Exception:
                continue

        elif tipo == "polilinea3d":
            puntos = figura["puntos"]
            msp.add_polyline3d(puntos, dxfattribs=dxf_attribs)

    layout = doc.layout()
    layout.add_line((0, 0), (210, 0), dxfattribs={"color": 6})
    layout.add_text("Plano generado", dxfattribs={"height": 10}).set_pos((10, 20))

    doc.saveas(filepath)

    try:
        matplotlib.qsave(msp, filepath.replace(".dxf", ".png"))
    except Exception:
        pass

    return filepath


@app.route("/", methods=["POST"])
def handle():
    try:
        data = request.get_json()

        if not data or "capas" not in data or "figuras" not in data:
            raise ValueError("Debes enviar un JSON válido con 'capas' y 'figuras'.")

        dxf_path = generar_dxf_desde_instrucciones(data)
        return send_file(
            dxf_path,
            as_attachment=True,
            download_name=os.path.basename(dxf_path),
            mimetype="application/dxf"
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json"
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
