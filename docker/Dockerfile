# Base image
FROM python:3.11-bookworm

# System deps (psycopg2 등 빌드 대비)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo \
    vim \
    bash-completion \
    ca-certificates \
    curl \
    git \
    build-essential \
    libpq-dev \
    pipx && \
    rm -rf /var/lib/apt/lists/*

# Add User
ARG USERNAME=developer
RUN adduser ${USERNAME} && \
    echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME}

USER ${USERNAME}
WORKDIR /home/${USERNAME}
# pipx 기본 경로 가용화
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# (옵션) 개인 프로필 파일 복사 경로가 있을 때만 사용
# COPY --chown=${USERNAME} ./docker/dev_profile/* .

# Install uv (via pipx)
RUN pipx ensurepath && pipx install "uv~=0.6"

# Dev 컨테이너는 에디터가 접속해서 명령 내리는 용도
CMD ["bash", "-lc", "sleep infinity"]