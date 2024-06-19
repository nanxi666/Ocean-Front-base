<template>
    <div>
        <div class="header">
            个人信息
        </div>
        <div class="body">
            <el-form ref="form" :model="form" label-width="23%" id="selectForm" :rules="form_rules">
                <el-form-item label="原密码：" prop="old_pwd">
                    <el-input v-model="form.old_pwd" type="password" show-password></el-input>
                </el-form-item>

                <el-form-item label="新密码：" prop="new_pwd">
                    <el-input v-model="form.new_pwd" type="password" show-password
                        placeholder="密码(包含大小写字母、数字，长度在6-12之间)"></el-input>
                </el-form-item>

                <el-form-item label="确认密码：" prop="confirm_pwd">
                    <el-input v-model="form.confirm_pwd" type="password" show-password></el-input>
                </el-form-item>
                <el-form-item style="text-align:center;">
                    <el-button type="primary" @click="change()">确定</el-button>
                </el-form-item>
            </el-form>
        </div>
    </div>
</template>

<script>
export default {
    created() {
        this.getdata()
    },
    data() {
        var checkPassword = (rule, value, cb) => {
            const regPassword = /(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).{6,12}$/;
            if (regPassword.test(value)) {

                return cb()
            }
            cb(new Error('密码应包含大写字母、小写字母、数字，长度在6-12位之间'))
        };
        var check_confirm_password = (rule, value, cb) => {
            var t = this.form.new_pwd && value && this.form.new_pwd !== value;

            if (!t) {
                return cb()
            }
            cb(new Error('两次密码不一致'))
        };
        return {
            form: {
                old_pwd: '',
                new_pwd: '',
                confirm_pwd: '',
            },
            form_rules: {
                old_pwd: [{ required: true, message: "必填", trigger: 'blur' }],
                new_pwd: [{ required: true, message: "必填", trigger: 'blur' }, { validator: checkPassword, trigger: 'blur' }],
                confirm_pwd: [{ required: true, message: "必填", trigger: 'blur' }, { validator: check_confirm_password, trigger: 'blur' }]
            }
        }
    },
    methods: {
        change() {
            this.$refs.form.validate(valid => {
                if (!valid)
                    return;
                else //验证通过再发送请求
                    if (this.form.confirm_pwd == this.form.new_pwd) {
                        this.$axios.post("/api/user/pwd_chg", this.form).then((res) => {
                            if (res.data.status == 200) {
                                this.$message({
                                    message: res.data.msg,
                                    type: "success"
                                })
                                this.form = {};
                            } else {
                                this.$message({
                                    message: res.data.msg,
                                    type: "error"
                                })
                            }
                        })
                    }
                    else {
                        this.$message({
                            message: "新密码与确认密码不一致",
                            type: "error"
                        })
                    }
            })
        }

    },
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
    width: 40%;
    /* margin: auto; */
    margin-top: 30px;
    margin-left: 30px;

}

#selectForm>>>.el-form-item__label {
    font-size: 18px;
}

span {
    font-size: 18px;
}
</style>