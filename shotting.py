import os
from google import genai
from PIL import Image
import streamlit as st

# 페이지 설정
st.set_page_config(
    page_title="🏀 Gemini AI 프로 슛폼 교정 코치", layout="wide"
)

# Gemini 클라이언트 초기화 (Streamlit Secrets 활용)
if "GEMINI_API_KEY" in st.secrets:
  client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
  st.error("Streamlit Secrets에 GEMINI_API_KEY가 설정되어 있지 않습니다.")
  st.stop()

st.title("🏀 Gemini AI 맞춤형 농구 슛폼 분석 및 교정 솔루션")
st.markdown(
    "자신의 슈팅 사진을 업로드하면, 모범 기준 슛폼 이미지들과 비교하여 **어느 부분을"
    " 어느 방향으로 고쳐야 하는지** 상세히 코칭해 드립니다."
)

# 1. 기준 이미지 로드 함수 (절대경로 및 최신 Streamlit 문법 적용)
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
      # use_column_width -> use_container_width 수정 완료
      st.sidebar.image(
          standard_images[label], caption=label, use_container_width=True
      )
    except Exception as e:
      st.sidebar.warning(f"{label} ({path}) 파일을 읽지 못했습니다: {e}")

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
    st.image(user_image, caption="분석 대상 사진", use_container_width=True)

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
        contents = [
            user_image,
            (
                "당신은 프로 농구 슈팅 전문 코치입니다. 위 사용자의 슛 사진을"
                " 분석하고, 아래 제공되는 모범 기준 이미지들과 비교해주세요.\n1."
                " 현재 자세 진단 (팔꿈치 각도, 무릎 굽힘, 밸런스)\n2. 모범"
                " 자세와의 차이점\n3. 구체적인 수정 방향 (예: 팔꿈치를 안쪽으로"
                " 5도 모으세요 등)\n4. 종합 총평 및 연습 방법"
            ),
        ]

        for label, img in standard_images.items():
          contents.append(img)
          contents.append(f"참고 모범 기준: [{label}]")

        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contents
        )

        with col2:
          st.empty()
          st.markdown("### 📊 상세 교정 리포트")
          st.write(response.text)

      except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {e}")
