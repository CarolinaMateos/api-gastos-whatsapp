from contextlib import asynccontextmanager

from fastapi import FastAPI, Form
from fastapi.responses import Response

from app.db import (
    init_db,
    create_expense,
    get_today_expenses,
    get_monthly_summary,
    delete_last_expense,
)
from app.parser import get_available_categories, parse_expense_message

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Backend de gastos por WhatsApp",
    lifespan=lifespan,
)

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "message": "Backend de gastos funcionando"
    }


@app.post("/whatsapp")
def whatsapp_webhook(
    Body: str = Form(default=""),
    From: str = Form(default="test-user"),
):
    message = Body.strip()
    user_phone = From.strip()

    if not message:
        return twiml_response("No he recibido ningún mensaje.")

    normalized_message = message.lower()

    if normalized_message == "resumen hoy":
        expenses = get_today_expenses(user_phone)
        total = sum(expense["amount"] for expense in expenses)

        return twiml_response(
            f"📊 Hoy llevas {total:.2f} € en {len(expenses)} gasto(s)."
        )

    if normalized_message == "resumen mes":
        summary = get_monthly_summary(user_phone)

        if not summary:
            return twiml_response(
                "Este mes todavía no tienes gastos guardados."
            )

        total = sum(row["total"] for row in summary)

        lines = [
            f"- {row['category']}: {row['total']:.2f} €"
            for row in summary
        ]

        return twiml_response(
            "📊 Resumen del mes:\n"
            + "\n".join(lines)
            + f"\n\nTotal: {total:.2f} €"
        )

    if normalized_message in {
        "categorias disponibles",
        "categorías disponibles",
        "categorias",
        "categorías",
    }:
        categories = get_available_categories()
        lines = [f"- {category}" for category in categories]

        return twiml_response(
            "Categorías disponibles:\n"
            + "\n".join(lines)
        )

    if normalized_message in {
        "eliminar ultimo",
        "eliminar último",
        "borrar ultimo",
        "borrar último",
    }:
        deleted_expense = delete_last_expense(user_phone)

        if not deleted_expense:
            return twiml_response(
                "No tienes gastos guardados para eliminar."
            )

        return twiml_response(
            f"Gasto eliminado #{deleted_expense['id']}\n"
            f"{deleted_expense['description']}: {deleted_expense['amount']:.2f} €\n"
            f"Categoría: {deleted_expense['category']}"
        )

    parsed_expense = parse_expense_message(message)

    if not parsed_expense:
        return twiml_response(
            "No entendí el gasto. Prueba con algo como:\n"
            "mercadona 23,50 comida"
        )

    saved_expense = create_expense(
        user_phone=user_phone,
        amount=parsed_expense["amount"],
        category=parsed_expense["category"],
        description=parsed_expense["description"],
        raw_message=message,
    )

    return twiml_response(
        f"✅ Gasto guardado #{saved_expense['id']}\n"
        f"{saved_expense['description']}: {saved_expense['amount']:.2f} €\n"
        f"Categoría: {saved_expense['category']}"
    )


def twiml_response(message):
    escaped_message = escape_xml(message)

    xml = f"""
<Response>
    <Message>{escaped_message}</Message>
</Response>
""".strip()

    return Response(content=xml, media_type="text/xml")


def escape_xml(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
