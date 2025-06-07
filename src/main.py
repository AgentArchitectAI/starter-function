import json

def main(context):
    req = context.req
    res = context.res

    try:
        raw_body = req.body
        context.log(f"[DEBUG] req.body: {raw_body!r}")  

        if not raw_body:
            raise ValueError("El cuerpo del request está vacío.")

        raw_input = json.loads(raw_body)
        context.log(f"[DEBUG] JSON nivel 1: {raw_input}")

        data_str = raw_input.get("data", "")
        if not data_str:
            raise ValueError("El campo 'data' está vacío o no presente.")

        data = json.loads(data_str)
        context.log(f"[DEBUG] JSON decodificado en 'data': {data}")

        prompt = data.get("prompt", "")
        context.log(f"[DEBUG] Prompt final: {prompt}")

        return res.json({
            "ok": True,
            "prompt": prompt
        })

    except Exception as e:
        context.error(f"[ERROR]: {str(e)}")
        return res.json({ "error": str(e) }, 500)
