<template>
  <div class="custom-empty">
    <div class="custom-empty__image">
      <svg viewBox="0 0 79 86" xmlns="http://www.w3.org/2000/svg">
        <g fill="none" fill-rule="evenodd">
          <g transform="translate(0 1)" fill="#AEB8C2">
            <ellipse cx="39.5" cy="42.5" rx="39.5" ry="42.5" opacity=".25" />
          </g>
          <path
            d="M55 12.76L44.854 1.258C44.367.474 43.656 0 42.907 0H21.093c-.749 0-1.46.474-1.947 1.257L9 12.761V22h46v-9.24z"
            fill="#AEB8C2"
          />
          <path
            d="M41.613 15.931c0-1.605.994-2.93 2.227-2.931H55v18.137C55 33.26 53.68 35 52.05 35h-40.1C10.32 35 9 33.259 9 31.137V13h11.16c1.233 0 2.227 1.323 2.227 2.928v.022c0 1.605 1.005 2.901 2.237 2.901h14.752c1.232 0 2.237-1.308 2.237-2.913v-.007z"
            fill="#F5F5F7"
          />
        </g>
      </svg>
    </div>
    <p class="custom-empty__description">{{ description }}</p>
    <slot />
  </div>
</template>

<script>
export default {
  name: 'CustomEmpty',
  props: {
    description: {
      type: String,
      default: '暂无数据'
    }
  }
}
</script>

<style scoped>
.custom-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.custom-empty__image {
  width: 80px;
  height: 80px;
}

.custom-empty__image svg {
  width: 100%;
  height: 100%;
}

.custom-empty__description {
  margin-top: 16px;
  color: #909399;
  font-size: 14px;
}
</style>
