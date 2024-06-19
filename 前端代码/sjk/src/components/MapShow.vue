<template>
    <div>
        <div class="header">
            地图查看
        </div>
        <div class="body">
            <div>
                <el-tag>选择日期:</el-tag>
                <el-date-picker v-model="date" range-separator="To" start-placeholder="Start date"
                    end-placeholder="End date">
                </el-date-picker>

                <el-tag style="margin-left: 50px">选择要素:</el-tag>
                <el-select v-model="factor" placeholder="Select" size="large" style="width: 100px">
                    <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>

                <el-button size="100px" type="success" style="margin-left: 50px;" @click="draw()">绘图</el-button>
            </div>

            <!-- <el-tag>{{ this.value }}</el-tag> -->
            <div>
                <el-image :src="imageSrc" fit="contain" :title="factor">

                </el-image>
            </div>

        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            value: '',
            date: '',
            factor: '',
            options: [
                { value: 'temperature', label: '温度' },
                { value: 'salinity', label: '盐度' },
                { value: 'density', label: '密度' }
            ],
            imageSrc: "",

        }
    },
    methods: {
        async draw() {
            this.$axios.request({
                method: "POST",
                url: "/api/manager/generate_image",
                timeout: 10 * 1000,
                data: {
                    time: this.date,
                    factor: this.factor,
                }
            }).then((res) => {
                this.value = res.data.image
                if (res.data.image) {
                    this.$message({
                        message: "绘制成功",
                        type: "success"
                    })
                    this.imageSrc = 'data:image/png;base64,' + res.data.image;
                }
                else {
                    this.$message({
                        message: "暂无相关数据",
                        type: "error"
                    })
                    this.imageSrc = null;
                }


            });


        }
    }
}
</script>

<style scoped>
.header {
    width: 100%;
    height: 10%;
    text-align: center;
    line-height: 64px;
    font-size: 20px;
    font-weight: 800;
    border-bottom: 1px solid #e3e3e3;
}

.body {

    width: 80%;
    margin: auto;
    margin-top: 30px;
}
</style>