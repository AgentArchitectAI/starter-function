import json

def main(context):
    req = context.req
    res = context.res

    try:
        data = req.body

        if not data:
            return res.json({"text": "MCP architect-dxf listo"})

        if isinstance(data, (str, bytes)):
            data = json.loads(data)

        if not isinstance(data, dict) or "prompt" not in data:
            raise ValueError("El campo 'prompt' es requerido en el JSON.")

        prompt = data["prompt"]

        filename = prompt.replace(" ", "_") + ".dxf"
        url = f"https://example.com/planos/{filename}"

        return res.json({
            "text": f"Plano generado para prompt: '{prompt}'\n Descargar DXF: {url}"
        })

    except Exception as e:
        context.error(f"[ERROR]: {str(e)}")
        return res.json({"text": f" Error: {str(e)}"}, 500)
