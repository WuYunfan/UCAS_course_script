import requests
import tkinter.messagebox
import tkinter
import threading
import time
from PIL import Image, ImageTk
import re


# 封装用于 post 的函数，失败返回 None
def post_data(url, data = None, params = None, time_out = 3, retry = 5):
    for _ in range(retry):
        try:
            page = sess.post(url, data = data, params = params, timeout=time_out)
            return page
        except:
            pass
    return None

def update_link():
    global Avatar, link_select_course, link_save_course, link_course_manage
    if Avatar == '本科生':
        link_select_course = 'http://jwxk.ucas.ac.cn/courseManageBachelor/selectCourse'  
        link_save_course = 'http://jwxk.ucas.ac.cn/courseManageBachelor/saveCourse'
        link_course_manage = 'http://jwxk.ucas.ac.cn/courseManageBachelor/main'
    else:
        link_select_course = 'http://jwxk.ucas.ac.cn/courseManage/selectCourse'
        link_save_course = 'http://jwxk.ucas.ac.cn/courseManage/saveCourse'
        link_course_manage = 'http://jwxk.ucas.ac.cn/courseManage/main'
    

def login_jwxt(add_id_to_name = 0):
    page_jump = post_data('http://sep.ucas.ac.cn/portal/site/226/821')
    if page_jump is None:
        tkinter.messagebox.showerror(title = '网页超时', message = '请检查是否断网或者延迟过高')
        return "high delay"

    pattern_jwxt_id = re.compile('Identity=([\w-]*)') # 匹配数字、字母、下划线和-
    try:
        iden = re.search(pattern_jwxt_id, page_jump.text).group(1)
    except:
        tkinter.messagebox.showerror(title = '未预料的错误', message = '没有成功匹配到Identity，请及时联系维护人员')
        login_info['text'] = '登录失败了\t\tT_T'
        # print(page.text)
        return

    jump_payload = {'Identity': iden}
    page_jwxt = post_data('http://jwxk.ucas.ac.cn/login', data=jump_payload)
    if page_jwxt is None:
        tkinter.messagebox.showerror(title = '网页超时', message = '请检查是否断网或者延迟过高')
        return "high delay"

    pattern_student_id = re.compile('doSelectNo\?num=([\w]*)')
    try:
        list_id = re.findall(pattern_student_id, page_jwxt.text)
        list_id.sort()
        N_id =len(list_id)
        student_id = list_id[N_id-1]

        for x in list_id: 
            print(x)

        student_number_payload = {'num': student_id}
        page_check = post_data('http://jwxk.ucas.ac.cn/doSelectNo', data = student_number_payload)
        if page_check is None:
            tkinter.messagebox.showerror(title = '网页超时', message = '请检查是否断网或者延迟过高')
            return "high delay"

        pattern_check = re.compile('</i> (.+?)&nbsp;\s*\(当前\)')
        id_check = re.search(pattern_check, page_check.text).group(1)
        if id_check != student_id:
            tkinter.messagebox.showerror(title = '内部错误', message = '选择学号失败，请及时联系维护人员')
            return "select student id fail"
        if add_id_to_name == 1:
            global name_student
            name_student = name_student + ' ' + student_id
        page_jwxt = page_check

    except:
        pass
        

    global Avatar
    list_bks = re.findall(re.compile('(bks)'), page_jwxt.text)
    print(list_bks)
    if len(list_bks) >0:
        Avatar = '本科生'
    else:
        Avatar = '研究生'

    #print(Avatar)
    update_link()
    global link_course_manage
    page_course_manage = post_data(link_course_manage)
    if page_course_manage is None:
        tkinter.messagebox.showerror(title = '网页超时', message = '请检查是否断网或者延迟过高')
        return "high delay"

    # 以下认为登录已经成功
    
    pattern_select_course_s = re.compile('\?s=(.*?)";')
    select_course_s = re.search(pattern_select_course_s, page_course_manage.text).group(1)

    pattern_deptIds = re.compile('label for="id_(\d+)"')
    deptIds = re.findall(pattern_deptIds, page_course_manage.text)
    
    global select_course_payload
    #select_course_payload = {'deptIds': deptIds}
    global query_s
    query_s = select_course_s
    select_course_payload = {'s': select_course_s, 'deptIds': deptIds}
    
    return 'ok'

def login(event = None):
    user = user_input.get()
    pwd = pwd_input.get()
    code = cert_code_input.get()
    login_payload = {'userName': user, 'pwd': pwd, 'certCode': code, 'sb': 'sb'}

    global login_info, root
    login_info['text'] = '登录SEP...\t\t=_ = '
    root.update_idletasks()

    # 尝试连接sep来登录
    page_after_login = post_data('http://sep.ucas.ac.cn/slogin', data = login_payload)
    if page_after_login is None:
        tkinter.messagebox.showerror(title = '网页超时', message = '请检查是否断网或者延迟过高')
        login_info['text'] = '登录失败了\t\tT_T'
        return
    # 判断是否仍停留在选课界面
    
    pattern_login_error = re.compile('<div class="alert alert-error">(.+?)</div>', re.S)
    try:
        err_type = re.search(pattern_login_error, page_after_login.text).group(1)
        tkinter.messagebox.showerror(title = '信息有误', message = err_type)
        if err_type == '密码错误':
            pwd_input.delete(0, tkinter.END)
        elif err_type == '验证码错误':
            cert_code_input.delete(0, tkinter.END)
        login_info['text'] = '登录失败了\t\tT_T'
        return
    except:
        pass # 信息没有错误

    # 尝试用正则表达式匹配姓名来判断是否成功进入sep主页面
    pattern_name = re.compile('"当前用户所在单位"> (.+?)&nbsp;(.+?)</li>', re.S)
    try:
        global name_student
        name_student = re.search(pattern_name, page_after_login.text).group(2)
        # print(name)
    except:
        tkinter.messagebox.showerror(title = '未能成功进入 SEP', message = '请仔细检查输入的用户名、密码以及验证码')
        login_info['text'] = '登录失败了\t\tT_T'
        return

    login_info['text'] = '登录选课系统...\t\t>_<'
    root.update_idletasks()

    res = login_jwxt(add_id_to_name = 1)
    
    if res != 'ok':
        login_info['text'] = '登录失败了\t\tT_T'
        return
    login_info['text'] = '欢迎 ' + name_student + ' ^_^'
    
    # 锁住登录信息（目前来看作用只是以防万一）
    #select_bachlor['state'] = tkinter.DISABLED
    #select_graduate['state'] = tkinter.DISABLED

def relogin():
    page_jump = post_data('http://sep.ucas.ac.cn/appStore')
    if page_jump is None:
        tkinter.messagebox.showerror(title = '请重新登录', message = '请检查是否断网或者延迟过高')
        return "high delay"

    pattern_offline = re.compile('SEP 教育业务接入平台')
    if re.search(pattern_offline, page_jump.text) != None:
        tkinter.messagebox.showerror(title = '请重新登录', message = '看起来已经好久没有操作了')
        return "sign out"
    
    res = login_jwxt()
    return res

def check_before_select():
    log['text'] = ''

    global select_course_payload, Avatar

    if Avatar is None:
        tkinter.messagebox.showerror(title = '错误', message = '您还未登录')
        global auto_working # 标记是否在捡漏，0 表示不在捡漏，1 表示在捡漏
        auto_working = 0
        jianlou_switch['text'] = '捡漏'
        return None

    global link_select_course
    page_select_course = post_data(link_select_course, select_course_payload)
    if page_select_course is None:
        select_result['text'] = '网页超时 没有进行选课'
        return None

    off_line = re.search('你的会话已失效或身份已改变，请重新登录', page_select_course.text)
    if off_line: # 至少已经从选课系统中掉线
        global login_info, root
        login_info['text'] = '掉线了，自动重连中...\t=_ = '
        root.update_idletasks()

        res = relogin()
        if res != 'ok': # 甚至从SEP系统中掉线
            init()
            select_result['text'] = '您已经掉线'
            login_info['text'] = '您已经掉线'
            return None
        else:
            login_info['text'] = '欢迎 ' + name_student + '\t^_^'
            root.update_idletasks()

            page_select_course = post_data(link_select_course, select_course_payload)
            if page_select_course is None:
                select_result['text'] = '网页超时 没有进行选课'
                return None

    system_closed = re.search('为了给您提供更好的服务', page_select_course.text)
    if system_closed:
        select_result['text'] = '选课系统未开放'
        return None

    select_result['text'] = '正在选课'
    return page_select_course

def generate_log(select_result_page):
    pattern = re.compile('class="success">(.+?)</label>')
    success_message = re.search(pattern, select_result_page.text)
    pattern = re.compile('class="error">(.+?)</label>')
    error_message = re.search(pattern, select_result_page.text)
    success = 0
    if success_message is not None:
        messages = success_message.group(1).split('<br/>')
        success = 1
    elif error_message is not None:
        messages = error_message.group(1).split('<br/>')
    else:
        messages = ['403 Forbidden']

    for single_message in messages:
        message_str = single_message
        if len(message_str) == 0:
            continue
        if len(message_str) > 25:
            message_str = message_str[:25] + '\n' + message_str[25:]
        if success:
            log_success['text'] += message_str + '\n' + sep_time['text'] + '\n'
        log['text'] += message_str + '\n' + sep_time['text'] + '\n'

def add_course_code_to_payload(course, select_course_page):
    pattern = re.compile('id="courseCode_(.*?)">%s' % course)
    course_code = re.search(pattern, select_course_page.text)
    if course_code is None:
        log['text'] += course + ': 该课程编码不可用（可能已经选过了）' + '\n' + sep_time['text'] + '\n'
        return 0
    else:
        select_course_payload['sids'].append(course_code.group(1))
        return 1

def list_split(list):
    list = re.split('[,，]',list)
    res = []
    for x in list: 
        x = x.strip()
        if x != '':
            res.append(x)
    return res

def get_csrftoken(select_course_page):
    global select_course_payload
    pattern_get_csrftoken = re.compile('name="_csrftoken" value="(.*?)"')
    value = re.search(pattern_get_csrftoken, select_course_page.text).group(1)
    select_course_payload['_csrftoken'] = value
    

def select_separately(event):
    select_course_page = check_before_select()
    if select_course_page is None:
        return

    course_list = list_split(course_input_separate.get())

    global Avatar, link_save_course, link_select_course
    
    sess.headers.update({"Referer": link_select_course + "?s=" + query_s})
    for course in course_list:
        select_course_page = check_before_select()
        select_course_payload['sids'] = []
        if add_course_code_to_payload(course, select_course_page) == 0:
            continue
        
        get_csrftoken(select_course_page)
        select_result_page = post_data(link_save_course, select_course_payload)
        if select_result_page is None:
            log['text'] += course + ': 网页超时'+' \n ' + sep_time['text'] + '\n'
        else:
            generate_log(select_result_page)
        del select_course_payload['_csrftoken']

    del sess.headers['Referer']
    select_result['text'] = '选课完成'

def select_together(event):
    select_course_page = check_before_select()
    if select_course_page is None:
        return

    course_list = list_split(course_input.get())

    select_course_payload['sids'] = []
    for course in course_list:
        add_course_code_to_payload(course, select_course_page)

    if len(select_course_payload['sids']) == 0:
        select_result['text'] = '课程代码均不可用'
        return

    global Avatar, link_save_course, link_select_course, link_course_manage
    
    get_csrftoken(select_course_page)
    sess.headers.update({"Referer": link_select_course + "?s=" + query_s})
    
    select_result_page = post_data(link_save_course + "?s=" + query_s, data = select_course_payload)
    
    del select_course_payload['_csrftoken']
    del sess.headers['Referer']
    
    #print(result_page.text)
    if select_result_page is None:
        select_result['text'] = '网页超时 没有进行选课'
    else:
        generate_log(select_result_page)
        select_result['text'] = '选课完成'


def get_time():
    while True:
        try:
            current_time = requests.get('http://jwxk.ucas.ac.cn/courseManage/main', timeout=3)
            current_time = current_time.headers
            current_time = current_time['Date']
            hour = current_time[17:19]
            minute = current_time[20:22]
            second = current_time[23:25]
            hour = (int(hour) + 8) % 24
            time_str = str(hour) + ':' + minute + ':' + second
            sep_time['text'] = time_str
            time.sleep(1)
            root.update_idletasks()
        except:
            pass

def auto_select():
    global auto_working
    global login_mark

    while True:
        if auto_working:
            select_separately(None)
        time.sleep(1)


def auto_switch(event):
    global auto_working

    if auto_working == 0:
        tkinter.messagebox.showinfo(title = '提示',
                 message = '1.请先使用“分开选”功能，确认提示信息为“超过限选人数”(而无其他错误)后再使用此功能\n'
                         '2.此模式每1s自动进行一次“分开选”（温馨提示：持续过长有风险）\n'
                         '3.如若中途掉线，需要自己手动重新登录')
        jianlou_switch['text'] = '停止'
    else:
        jianlou_switch['text'] = '捡漏'
    auto_working = 1 - auto_working


def download_image_file(event):
    global sess, login_info

    login_info['text'] = ''
    try:
        html = sess.get('http://sep.ucas.ac.cn/randomcode.jpg', timeout = 3)
    except:
        login_info['text'] = '网页超时 请重新获取验证码'
        return

    fp = open("certcode.jpg", 'wb')
    fp.write(html.content)
    fp.close()

    global cert_photo, show_pic
    cert_img = Image.open("certcode.jpg")
    cert_img = cert_img.resize((100, 25), Image.ANTIALIAS) # 调整大小 Image.ANTIALIAS 抗锯齿
    cert_photo = ImageTk.PhotoImage(cert_img)
    show_pic['image'] = cert_photo

    cert_code_input.delete(0, tkinter.END)

# 初始化
def init():
    # 全局变量
    global select_course_payload # 用于选课的 payload，记录用于选课的 cid 和 要选的课程编号
    select_course_payload = None

    global auto_working # 标记是否在捡漏，0 表示不在捡漏，1 表示在捡漏
    auto_working = 0
    jianlou_switch['text'] = '捡漏'

    global sess # 全局session
    sess = requests.session()
    sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.84'}) # 给 seesion 做伪装，通过浏览器检测

    global Avatar # 标明用本科生/研究生身份登录
    Avatar = None

    download_image_file(None)

    #select_bachlor['state'] = tkinter.NORMAL
    #select_graduate['state'] = tkinter.NORMAL


def sign_out():
    global Avatar
    if Avatar == None:
        tkinter.messagebox.showerror(title = 'Error', message = '您尚未登录')
        return
    init()
    login_info['text'] = '成功下线'

if __name__ == "__main__":
    global root
    root = tkinter.Tk()
    root.title("UCAS_course")
    root.geometry('615x580')
    root.resizable(width = False, height = False)

    menubar = tkinter.Menu(root)
    menubar.add_command(label = "下线", command = sign_out)
    root.config(menu = menubar)

    sep_time = tkinter.Label(root, font = ('Calibri', '10'))
    sep_time.grid(row = 0, column = 1, sticky = tkinter.E) #紧贴右侧

    thread_time = threading.Thread(target = get_time)
    thread_time.setDaemon(True)
    thread_time.start()

    global login_info
    login_info = tkinter.Label(root, text = '')
    login_info.grid(row = 6, column = 0, sticky = tkinter.W) #紧贴左侧
    login_info['font'] = ('Calibri', '14')

    tkinter.Label(root, text = '用户名(同sep)', font = ('Calibri', '14')).grid(row = 0, column = 0, sticky = tkinter.W)
    user_input = tkinter.Entry(root)
    user_input.grid(row = 1, column = 0, sticky = tkinter.W)
    user_input['font'] = ('Calibri', '14')
    user_input['width'] = 30

    tkinter.Label(root, text = '密码', font=('Calibri', '14')).grid(row = 0, column = 1, sticky = tkinter.W)
    pwd_input = tkinter.Entry(root)
    pwd_input['show'] = '*'
    pwd_input['width'] = 30
    pwd_input.grid(row = 1, column = 1, sticky = tkinter.W)
    pwd_input['font'] = ('Calibri', '14')
    pwd_input.bind('<Key-Return>', login)

    # 验证码 Frame
    frame_cert = tkinter.Frame(master = root, bd = 0, relief = tkinter.RAISED, width = 1)
    frame_cert.grid(row = 2, column = 0, sticky = tkinter.W)
    # text
    tkinter.Label(master = frame_cert, text = '验证码', font = ('Calibri', '14')).pack(side = tkinter.LEFT, padx = 0)
    # input entry
    global cert_code_input
    cert_code_input = tkinter.Entry(master = frame_cert)
    cert_code_input['width'] = 5
    cert_code_input.pack(side = tkinter.LEFT, padx = 4)
    cert_code_input['font'] = ('Calibri', '14')
    cert_code_input.bind('<Key-Return>', login)
    # picture
    global show_pic
    show_pic = tkinter.Label(master = frame_cert)
    show_pic.pack(side = tkinter.LEFT, padx = 4)
    # buttom
    get_pic = tkinter.Button(master = frame_cert, text = '刷新')
    get_pic.pack(side = tkinter.LEFT, padx = 4)
    get_pic['width'] = 5
    get_pic['font'] = ('Calibri', '14')
    get_pic.bind('<ButtonRelease-1>', download_image_file)
    get_pic.bind('<Key-Return>', download_image_file)

    # 选择身份
    '''
    global avatar_input
    avatar_input = tkinter.StringVar() # 定义变量记录所选身份
    avatar_input.set('本科生')
    frame_avatar = tkinter.Frame(master = root, bd = 0, relief = tkinter.RAISED, width = 1)
    frame_avatar.grid(row = 2, column = 1, sticky = tkinter.W)
    select_bachlor = tkinter.Radiobutton(frame_avatar, text = '本科生', variable = avatar_input, value = '本科生') # 默认设置本科生
    select_bachlor.pack(side = tkinter.LEFT, padx = 4)
    select_bachlor.bind('<Key-Return>', login)
    select_graduate = tkinter.Radiobutton(frame_avatar, text = '研究生', variable = avatar_input, value = '研究生')
    select_graduate.pack(side = tkinter.LEFT, padx = 4)
    select_graduate.bind('<Key-Return>', login)
    #print(avatar_input.get())
    '''

    login_button = tkinter.Button(root, text = '登 录')
    login_button['width'] = 6
    login_button['font'] = ('Calibri', '14')
    login_button.grid(row = 6, column = 1, sticky = tkinter.E)
    login_button.bind('<ButtonRelease-1>', login)
    login_button.bind('<Key-Return>', login)

    select_result = tkinter.Label(root, text = '')
    select_result.grid(row = 9, sticky = tkinter.W)
    select_result['font'] = ('Calibri', '14')

    tkinter.Label(root, text = '课程编码（一起选） 用逗号分隔', font = ('Calibri', '14')).grid(row = 7, column = 0, sticky = tkinter.W)
    course_input = tkinter.Entry(root)
    course_input['width'] = 30
    course_input.grid(row = 8, column = 0, sticky = tkinter.W)
    course_input['font'] = ('Calibri', '14')
    course_input.bind('<Key-Return>', select_together)

    tkinter.Label(root, text = '课程编码（分开选） 用逗号分隔', font=('Calibri', '14')).grid(row = 7, column = 1, sticky = tkinter.W)
    course_input_separate = tkinter.Entry(root)
    course_input_separate['width'] = 30
    course_input_separate.grid(row = 8, column = 1, sticky = tkinter.W)
    course_input_separate['font'] = ('Calibri', '14')
    course_input_separate.bind('<Key-Return>', select_separately)

    course_choose = tkinter.Button(root, text = '一起选')
    course_choose.bind('<ButtonRelease-1>', select_together)
    course_choose['font'] = ('Calibri', '14')
    course_choose['width'] = 6
    course_choose.grid(row = 9, column = 0, sticky = tkinter.E)

    course_choose = tkinter.Button(root, text = '分开选')
    course_choose.bind('<ButtonRelease-1>', select_separately)
    course_choose['font'] = ('Calibri', '14')
    course_choose['width'] = 6
    course_choose.grid(row = 9, column = 1, sticky = tkinter.E)

    jianlou_switch = tkinter.Button(root, text = '捡 漏')
    jianlou_switch.bind('<ButtonRelease-1>', auto_switch)
    jianlou_switch['font'] = ('Calibri', '14')
    jianlou_switch['width'] = 6
    jianlou_switch.grid(row = 9, column = 1, sticky = tkinter.W)

    tkinter.Label(root, text = 'Log:', font=('Calibri', '14')).grid(row = 11, column = 0, sticky = tkinter.W)
    log = tkinter.Label(root, anchor = 'nw', justify = 'left', background = 'white', relief = 'sunken', height = 21, width = 50,
                        borderwidth = 2)
    log.grid(row = 12, column = 0, sticky = tkinter.W)
    log['font'] = ('Calibri', '9')

    tkinter.Label(root, text = 'Log_Success:', font=('Calibri', '14')).grid(row = 11, column = 1, sticky = tkinter.W)
    log_success = tkinter.Label(root, anchor = 'nw', justify = 'left', background = 'white', relief = 'sunken', height = 21,
                                width = 50, borderwidth = 2)
    log_success.grid(row = 12, column = 1, sticky = tkinter.W)
    log_success['font'] = ('Calibri', '9')

    init()
    thread_auto_select = threading.Thread(target = auto_select)
    thread_auto_select.setDaemon(True)
    thread_auto_select.start()
    root.mainloop()
