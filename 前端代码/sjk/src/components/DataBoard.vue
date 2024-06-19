<template>
    <div>
        <div class="header">
            数据表
        </div>
        <div class="body">
            <el-tag>选择日期:</el-tag>
            <el-date-picker v-model="daterange" type="daterange" range-separator="To" start-placeholder="Start date"
                end-placeholder="End date">
            </el-date-picker>

            <el-button size="100px" type="success" style="margin-left: 50px;" @click="getdata()">查询</el-button>

            <el-table :data="tableData" style="width: 89%" class="table">
                <el-table-column prop="time" label="时间" width="200" align="center">
                </el-table-column>
                <el-table-column prop="longitude" label="经度" width="100" align="center">
                </el-table-column>
                <el-table-column prop="latitude" label="纬度" width="100" align="center">
                </el-table-column>
                <el-table-column prop="depth" label="深度" width="100" align="center">
                </el-table-column>

                <el-table-column prop="temperature" label="温度" width="100" align="center">
                </el-table-column>
                <el-table-column prop="salinity" label="盐度" width="100" align="center">
                </el-table-column>
                <el-table-column prop="density" label="密度" width="100" align="center">
                </el-table-column>

                <!-- <el-table-column width="120" align="center">
                    <template slot="header">
                        <el-button icon="el-icon-plus" size="small" type="success" @click="showdia_add()">添加服务员
                        </el-button>
                    </template>
                </el-table-column> -->

            </el-table>

        </div>
    </div>
</template>

<script>

export default {
    data() {
        return {
            daterange: [],
            tableData: [],
            msg: '',
        }
    },
    methods: {
        async getdata() {
            this.$axios.request({
                method: "POST",
                url: "/api/manager/getdata",
                data: {
                    time: this.daterange,
                    longitude: null,
                    latitude: null,
                    depth: null
                },
                timeout: 10 * 1000,

            }).then((res) => {
                if (res.data.status == 200) {
                    this.$message({
                        message: res.data.msg,
                        type: "success"
                    })
                    this.tableData = res.data.data

                }
                else {
                    this.$message({
                        message: res.msg + "Error Code:" + res.status,
                        type: "error"
                    })
                }

            })

        },

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