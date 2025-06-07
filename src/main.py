import json
import ezdxf
import tempfile
import os
import uuid
from appwrite.client import Client
from appwrite.services.storage import Storage

def draw_architectural_plan(doc, prompt_text):
    msp = doc.modelspace()
    msp.add_lwpolyline([
        (0, 0), (6000, 0), (6000, 4000), (0, 4000), (0, 0)
    ], dxfattribs={"closed": True})
    msp.add_text(prompt_text, dxfattribs={
        'height': 250,
        'layer': 'TEXT'
    }).set_pos((100, 3800), align='LEFT')

def main(context):
    req = context.req
    res = context.res

    try:
        data = req.body
        context.log(f"[MCP] Tipo de req.body: {type(data)}")

        if not data or (isinstance(data, (str, bytes)) and not data.strip()):
            context.log("[MCP] Agent Zero hizo ping (POST vacío)")
            return res.json({"text": " MCP architect-dxf activo y listo."})

        if isinstance(data, (str, bytes)):
            data = json.loads(data)

        context.log(f"[MCP] Contenido recibido: {data}")

        if not isinstance(data, dict) or "prompt" not in data:
            raise ValueError("Falta el campo 'prompt'.")

        prompt = data["prompt"]
        context.log(f"[MCP] Prompt recibido: {prompt}")

        filename = prompt.replace(" ", "_") + ".dxf"

        doc = ezdxf.new()
        draw_architectural_plan(doc, prompt)

        
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        doc.saveas(temp_path)
        context.log(f"[MCP] Archivo generado en: {temp_path}")
        client = Client()
        client.set_endpoint(os.environ["APPWRITE_ENDPOINT"])
        client.set_project(os.environ["APPWRITE_PROJECT_ID"])
        client.set_key(os.environ["APPWRITE_API_KEY"])

        storage = Storage(client)


        file_id = uuid.uuid4().hex
        with open(temp_path, "rb") as file:
            result = storage.create_file(
                bucket_id=os.environ["APPWRITE_BUCKET_ID"],
                file_id=file_id,
                file=file,
                read=["*"],  
                write=[]
            )

        download_url = f'{os.environ["APPWRITE_ENDPOINT"].rstrip("/")}/storage/buckets/{os.environ["APPWRITE_BUCKET_ID"]}/files/{file_id}/download?project={os.environ["APPWRITE_PROJECT_ID"]}'

        context.log(f"[MCP] Archivo subido. URL: {download_url}")

        return res.json({
            "text": f" Plano generado con éxito.\n Descargar DXF: {download_url}"
        })

    except Exception as e:
        context.error(f"[ERROR MCP]: {str(e)}")
        return res.json({"text": f" Error: {str(e)}"}, 500)
