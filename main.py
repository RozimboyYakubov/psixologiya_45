import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

# Bot tokeningiz
TOKEN = "8257613052:AAFeuLINYi5qIPSMgkHbVri5W-0LCK1wXRM"

# Psixologlar (Adminlar) ID ro'yxati (2 ta ID kiritilgan)
PSYCHOLOG_CHAT_IDS = [5825744781, 978885607]  # 👈 Ikkinchi ID'ni o'zingiznikiga o'zgartirib qo'ying

bot = Bot(token=TOKEN)
router = Router()

# FSM holatlari
class MurojaatState(StatesGroup):
    waiting_for_problem_text = State()

class PsixologReplyState(StatesGroup):
    waiting_for_reply_text = State()

class TestState(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()


# --- MENYULAR ---

def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Anonim murojaat qilish", callback_data="report_problem")],
            [InlineKeyboardButton(text="🧠 Psixologik test (Stress testi)", callback_data="start_test")],
        ]
    )

def get_categories_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 O‘qish va darslar", callback_data="cat_study")],
            [InlineKeyboardButton(text="👥 Tengdoshlar bilan munosabat", callback_data="cat_friends")],
            [InlineKeyboardButton(text="🏠 Oila va ota-ona", callback_data="cat_family")],
            [InlineKeyboardButton(text="😰 Stress va xavotir", callback_data="cat_stress")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")],
        ]
    )


# --- START KOMANDASI ---

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "Assalomu aleykum! Men maktab psixologi Feruza Otabekovna.\n"
        "Bu yerda muammolaringizni yozishingiz mumkin. Hammasi to‘liq anonim tarzda qabul qilinadi."
    )
    await message.answer(text, reply_markup=get_main_menu(), parse_mode="Markdown")


# --- ANONIM MUROJAAT QISMI ---

@router.callback_query(F.data == "report_problem")
async def report_problem_handler(callback: CallbackQuery):
    await callback.message.edit_text(
        "Qaysi yo'nalishda muammoyingiz bor? Quyidagilardan birini tanlang:",
        reply_markup=get_categories_menu()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cat_"))
async def category_selected(callback: CallbackQuery, state: FSMContext):
    categories = {
        "cat_study": "O‘qish va darslar",
        "cat_friends": "Tengdoshlar bilan munosabat",
        "cat_family": "Oila va ota-ona",
        "cat_stress": "Stress va xavotir",
    }
    selected_cat = categories.get(callback.data, "Boshqa")
    
    await state.update_data(category=selected_cat)
    await callback.message.edit_text(
        f"Tanlangan mavzu: *{selected_cat}*\n\n"
        "Iltimos, muammoyingizni batafsil yozib yuboring (faqat matn ko'rinishida):",
        parse_mode="Markdown"
    )
    await state.set_state(MurojaatState.waiting_for_problem_text)
    await callback.answer()

@router.message(MurojaatState.waiting_for_problem_text)
async def receive_problem(message: Message, state: FSMContext):
    data = await state.get_data()
    category = data.get("category")
    student_id = message.from_user.id
    
    report_text = (
        f"🚨 *Yangi anonim murojaat!*\n\n"
        f"📂 *Kategoriya:* {category}\n"
        f"📝 *Murojaat matni:* {message.text}"
    )
    
    reply_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Javob yozish", callback_data=f"reply_{student_id}")]
        ]
    )
    
    sent_successfully = False

    # Barcha adminlarga (psixologlarga) xabar yuborish
    for admin_id in PSYCHOLOG_CHAT_IDS:
        try:
            await message.bot.send_message(
                chat_id=admin_id,
                text=report_text,
                reply_markup=reply_keyboard,
                parse_mode="Markdown"
            )
            sent_successfully = True
        except Exception as e:
            logging.error(f"Admin {admin_id} ga xabar yuborishda xatolik: {e}")

    if sent_successfully:
        await message.answer(
            "✅ Murojaatingiz psixologga muvaffaqiyatli va anonim tarzda yuborildi!\n\n"
            "💡 *Iltimos, Telegramni kuzatib turing, psixologimiz tez orada siz bilan bog'lanadi va javob yozadi.*",
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❌ Xatolik yuz berdi. Xabar psixologga yetib bormadi. Iltimos keyinroq urinib ko'ring.",
            reply_markup=get_main_menu()
        )
    
    await state.clear()


# --- PSIXOLOGNING JAVOB BERISH JARAYONI ---

@router.callback_query(F.data.startswith("reply_"))
async def psych_start_reply(callback: CallbackQuery, state: FSMContext):
    student_id = int(callback.data.split("_")[1])
    await state.update_data(target_student_id=student_id)
    
    await callback.message.answer(
        "✍️ O'quvchiga yubormoqchi bo'lgan javobingizni yozing (matn ko'rinishida):"
    )
    await state.set_state(PsixologReplyState.waiting_for_reply_text)
    await callback.answer()

@router.message(PsixologReplyState.waiting_for_reply_text)
async def psych_send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    student_id = data.get("target_student_id")
    
    try:
        await message.bot.send_message(
            chat_id=student_id,
            text=f"📬 *Psixologdan javob keldi:*\n\n{message.text}",
            parse_mode="Markdown"
        )
        await message.answer("✅ Javobingiz o'quvchiga muvaffaqiyatli yetkazildi!")
    except Exception:
        await message.answer("❌ Xatolik: O'quvchi botni bloklagan bo'lishi mumkin yoki xabar yuborib bo'lmadi.")
    
    await state.clear()


# --- PSIXOLOGIK TEST QISMI ---

@router.callback_query(F.data == "start_test")
async def start_psych_test(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(TestState.q1)
    await state.update_data(score=0)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1. Hech qachon / Kamdan-kam", callback_data="q1_0")],
        [InlineKeyboardButton(text="2. Ba'zida", callback_data="q1_1")],
        [InlineKeyboardButton(text="3. Ko'p hollarda / Har doim", callback_data="q1_2")],
    ])
    
    await callback.message.edit_text(
        "🧠 **Stress va Xavotir testi**\n\n1-savol: Oxirgi paytlarda sababsiz charchoq yoki holsizlikni his qilyapsizmi?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(TestState.q1, F.data.startswith("q1_"))
async def process_q1(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split("_")[1])
    await state.update_data(score=score)
    await state.set_state(TestState.q2)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1. Yo'q", callback_data="q2_0")],
        [InlineKeyboardButton(text="2. Ba'zida bo'ladi", callback_data="q2_1")],
        [InlineKeyboardButton(text="3. Ha, tez-tez asabiylashaman", callback_data="q2_2")],
    ])
    
    await callback.message.edit_text(
        "🧠 **Stress va Xavotir testi**\n\n2-savol: Kichik narsalarga ham tez achchiqlanib yoki asabiylashib ketasizmi?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(TestState.q2, F.data.startswith("q2_"))
async def process_q2(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_score = data.get("score", 0) + int(callback.data.split("_")[1])
    await state.update_data(score=current_score)
    await state.set_state(TestState.q3)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1. Yaxshi uxlayman", callback_data="q3_0")],
        [InlineKeyboardButton(text="2. Qiyinchilik bilan uxlayman", callback_data="q3_1")],
        [InlineKeyboardButton(text="3. Umuman uxlay olmayman / Yomon tushlar ko'raman", callback_data="q3_2")],
    ])
    
    await callback.message.edit_text(
        "🧠 **Stress va Xavotir testi**\n\n3-savol: Uyqu rejimingiz qanday? Kechalari o'ylanib uxlashga qiynalasizmi?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(TestState.q3, F.data.startswith("q3_"))
async def process_q3(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    total_score = data.get("score", 0) + int(callback.data.split("_")[1])
    
    if total_score <= 1:
        result_text = "🟢 **Natija: Hammasi joyida!**\nSizda stress darajasi past. Ruhiy holatingiz barqaror."
    elif total_score <= 4:
        result_text = "🟡 **Natija: O‘rtacha stress holati.**\nSiz biroz charchagansiz. Dam olishga, sevimli mashg'ulotlarga vaqt ajratishingiz kerak."
    else:
        result_text = "🔴 **Natija: Yuqori darajadagi stress yoki xavotir!**\nSizda biroz zo'riqish yuqori ekan. Iltimos, yuqoridagi **Anonim murojaat** tugmasi orqali psixologga yozib ko'ring, yolg'iz emassiz!"

    await callback.message.edit_text(
        f"{result_text}\n\nTest yakunlandi. Yana nima qilamiz?",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()


# --- ORQAGA TUGMASI ---

@router.callback_query(F.data == "back_home")
async def back_home_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Asosiy menyu:", reply_markup=get_main_menu())
    await callback.answer()


# --- ASOSIY ISHGA TUSHIRISH ---

async def main():
    logging.basicConfig(level=logging.INFO)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
