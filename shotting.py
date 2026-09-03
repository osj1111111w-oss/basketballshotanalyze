import os
from google import genai
from google.genai import types
from PIL import Image
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="🏀 Gemini AI 프로 슛폼 교정 코치", layout="wide"
)

# Gemini 클라이언트 초기화 (Streamlit Secrets에서 키 가져오기)
if "GEMINI_API_KEY" in st.secrets:
  client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
  st.error(
      "Streamlit Secrets에 GEMINI_API_KEY가 설정되어 있지 않습니다. 설정을"
      " 확인해주세요!"
  )
  st.stop()

st.title("🏀 Gemini AI 맞춤형 농구 슛폼 분석 및 교정 솔루션")
st.markdown(
    "자신의 슈팅 사진을 업로드하면, 모범 기준 슛폼 이미지들과 비교하여 **어느 부분을"
    " 어느 방향으로 고쳐야 하는지** 상세히 코칭해 드립니다."
)

# 1. 기준 이미지 로드 함수 (저장소 내 파일 활용)
# 1. 기준 이미지 로드 함수 (현재 shotting.py 파일의 위치 기준 경로 설정)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

standard_images = {}
standard_paths = {
    "준비 자세 (Standard 1)": os.path.join(BASE_DIR, "standardshot1.jpg"),
    "조준 및 셋포인트 (Standard 2)": os.path.join(BASE_DIR, "standardshot2.jpg"),
    "슈팅 릴리즈 (Standard 3)": os.path.join(BASE_DIR, "standardshot3.jpg"),
    "팔로우 스루 (Standard 4)": os.path.join(BASE_DIR, "standardshot4.jpg"),
}

st.sidebar.header("📋 프로 선수/모범 기준 슛폼 참고")
for label, path in standard_paths.items():
  if os.path.exists(path):
    try:
      standard_images[label] = Image.open(path)
      st.sidebar.image(
          standard_images[label], caption=label, use_column_width=True
      )
    except Exception as e:
      st.sidebar.warning(f"{label} ({path}) 파일을 읽지 못했습니다: {e}")
  else:
      st.sidebar.info(f"'{path}' 파일이 깃허브에 없습니다. (선택사항)")

# 2. 사용자 입력 섹션
st.divider()
uploaded_file = st.file_uploader(
    "📸 분석할 본인의 농구 슛 사진을 업로드하세요",
    type=["jpg", "jpeg", "png"],
)

if uploaded_file is not None:
  col1, col2 = st.columns(2)

  with col1:
    st.subheader("사용자 업로드 슛")
    user_image = Image.open(uploaded_file)
    st.image(
        user_image, caption="분석 대상 사진", use_column_width=True
    )

  with col2:
    st.subheader("🎯 AI 코칭 피드백 대기중")
    st.info(
        "아래 버튼을 누르면 모범 슛폼 기준과 비교하여 신체 각도 및 수정 방향을"
        " 진단합니다."
    )

  if st.button("🚀 내 슛폼 정밀 분석 및 피드백 받기", type="primary"):
    with st.spinner(
        "Gemini AI가 모범 기준 이미지와 대조하여 각도와 자세를 정밀 분석 중입니다..."
    ):
      try:
        # Gemini에 보낼 콘텐츠 리스트 구성
        contents = [
            user_image,
            (
                "당신은 프로 농구 슈팅 전문 코치입니다. "
                "위 사용자의 슛 사진을 분석하고, 만약 사이드바나 저장소에 제공된 모범 기준 이미지"
                "(standardshot1~4.jpg)가 있다면 그 이상적인 자세와 비교해주세요. "
                "단순한 일치도 점수 매기기에 그치지 말고, 다음 항목을 포함하여 아주 구체적으로 가이드해 주세요:\n\n"
                "1. **현재 자세 진단**: 팔꿈치 각도, 무릎 굽힘 정도, 밸런스, 릴리즈 타이밍 평가\n"
                "2. **모범 자세와의 차이점**: 기준 폼과 비교했을 때 부족하거나 틀어진 부분 지적\n"
                "3. **구체적인 수정 방향 (Actionable Feedback)**: "
                "'팔꿈치를 안쪽으로 5도 모으세요', '무릎을 좀 더 굽혀서 하체 탄력을 쓰세요' 등 "
                "어느 방향으로 어떻게 고쳐야 하는지 실천 가능한 교정 팁\n"
                "4. **종합 총평 및 연습 방법**"
            ),
        ]

        # 사용 가능한 기준 이미지들도 함께 전송 모델에 포함 (멀티모달 활용)
        for label, img in standard_images.items():
          contents.append(img)
          contents.append(f"위 이미지는 참고용 모범 기준인 [{label}] 입니다.")

        # Gemini 2.5 Flash 모델 호출 (최신 SDK 문법 적용)
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contents
        )

        with col2:
          st.empty()  # 기존 안내 메시지 초기화
          st.markdown("### 📊 상세 교정 리포트")
          st.write(response.text)

      except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {e}")
