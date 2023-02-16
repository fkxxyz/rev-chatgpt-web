<template>
  <div>{{ data }}</div>
</template>

<script>
import api from "./api"
export default {
  name: 'App',
  components: {
  },
  data: function () {
    return {
      data: '',
    }
  },
  created() {
    api.ping().then(data => {
      this.data = data.data
    })
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
