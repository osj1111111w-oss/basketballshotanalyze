import os
import cv2
import mediapipe as mp
import numpy as np
import streamlit as st

# Streamlit 페이지 설정
st.set_page_config(
    page_title="농구 슛폼 분석기", page_icon="농구", layout="centered"
)

st.title(" 농구 슛폼 분석기")
st.write(
    "내 슛폼 사진을 업로드하면 서버에 등록된 정석 슛폼들과 비교하여 일치율을"
    " 측정합니다."
)
st.info("💡 기준 일치율 **80% 이상** 시 **통과** 처리됩니다!")

# MediaPipe Pose 설정
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)


def calculate_angle(a, b, c):
  """세 점(a, b, c) 사이의 각도를 계산하는 함수 (b가 꼭짓점)"""
  a = np.array(a)  # 첫 번째 관절 (예: 어깨 또는 골반)
  b = np.array(b)  # 중심 관절 (예: 팔꿈치 또는 무릎)
  c = np.array(c)  # 마지막 관절 (예: 손목 또는 발목)

  radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(
      a[1] - b[1], a[0] - b[0]
  )
  angle = np.abs(radians * 180.0 / np.pi)

  if angle > 180.0:
    angle = 360 - angle
  return angle


def get_shooting_angles(image):
  """이미지에서 오른쪽 팔꿈치 각도와 오른쪽 무릎 각도 추출"""
  image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
  results = pose.process(image_rgb)

  if not results.pose_landmarks:
    return None

  landmarks = results.pose_landmarks.landmark

  try:
    # 오른쪽 팔 (어깨: 12, 팔꿈치: 14, 손목: 16)
    shoulder = [
        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y,
    ]
    elbow = [
        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
        landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y,
    ]
    wrist = [
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
        landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y,
    ]
    elbow_angle = calculate_angle(shoulder, elbow, wrist)

    # 오른쪽 다리 (골반/엉덩이: 24, 무릎: 26, 발목: 28)
    hip = [
        landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,
        landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y,
    ]
    knee = [
        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,
        landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y,
    ]
    ankle = [
        landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,
        landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y,
    ]
    knee_angle = calculate_angle(hip, knee, ankle)

    return {"elbow_angle": elbow_angle, "knee_angle": knee_angle}
  except Exception:
    return None


# 1. 정석 사진 파일명 목록 정의 (원하시는 만큼 추가 가능)
STANDARD_IMAGE_FILES = [
    "standardshot1.jpg",
    "standardshot2.jpg",
    "standardshot3.jpg",
    "standardshot4.jpg",
]

# 사용자 슛폼 사진 업로드
user_file = st.file_uploader(
    "📸 나의 슛폼 사진을 업로드하세요", type=["jpg", "jpeg", "png"]
)

if user_file is not None:
  # 서버에 존재하는 정석 사진들만 불러오기
  valid_standard_images = []
  for std_file in STANDARD_IMAGE_FILES:
    if os.path.exists(std_file):
      valid_standard_images.append(std_file)

  if not valid_standard_images:
    st.error(
        "⚠️ 서버에 정석 슛폼 사진이 없습니다! 프로그램이 실행 중인 폴더에"
        " `standard_1.jpg`, `standard_2.jpg` 등의 이름으로 정석 사진을"
        " 넣어주세요."
    )
  else:
    # 사용자 이미지 읽기
    file_bytes_user = np.asarray(bytearray(user_file.read()), dtype=np.uint8)
    user_img = cv2.imdecode(file_bytes_user, 1)

    st.subheader("업로드된 내 슛폼 사진")
    st.image(user_img, channels="BGR", width=400)

    if st.button("🚀 슛폼 분석 시작하기", type="primary"):
      with st.spinner("AI가 여러 정석 슛폼과 비교 분석 중입니다..."):
        user_angles = get_shooting_angles(user_img)

        if user_angles is None:
          st.error(
              "❌ 사람의 관절을 인식하지 못했습니다. 전신 또는 상체가 선명하게"
              " 나온 사진으로 다시 시도해 주세요."
          )
        else:
          similarities = []

          # 여러 장의 정석 사진과 각각 비교
          for std_path in valid_standard_images:
            std_img = cv2.imread(std_path)
            std_angles = get_shooting_angles(std_img)

            if std_angles is not None:
              # 팔꿈치와 무릎 각도 차이 계산
              elbow_diff = abs(
                  std_angles["elbow_angle"] - user_angles["elbow_angle"]
              )
              knee_diff = abs(
                  std_angles["knee_angle"] - user_angles["knee_angle"]
              )

              # 각도 차이를 바탕으로 일치율 계산 (오차가 클수록 점수 하락)
              elbow_sim = max(0, 100 - (elbow_diff * 1.5))
              knee_sim = max(0, 100 - (knee_diff * 1.5))

              # 종합 일치율 (팔 60%, 무릎 40% 가중치)
              total_sim = (elbow_sim * 0.6) + (knee_sim * 0.4)
              similarities.append(total_sim)

          if similarities:
            # 여러 정석 중 가장 높은 일치율 채택
            best_similarity = max(similarities)

            st.divider()
            st.metric(
                label="🏆 최고 슛폼 일치율", value=f"{best_similarity:.1f}%"
            )

            if best_similarity >= 80:
              st.success(
                  "🎉 **통과 (Pass)!** 훌륭한 슛폼입니다! 정석 자세와 일치합니다."
              )
              st.balloons()
            else:
              st.error(
                  "❌ **실패 (Fail)!** 정석 슛폼과 일치율이 80%를 넘지"
                  " 못했습니다. 팔꿈치 각도나 자세를 교정해 보세요!"
              )
          else:
            st.warning(
                "⚠️ 정석 사진들에서 관절을 추출할 수 없습니다. 정석 사진을"
                " 교체해 주세요."
            ) 