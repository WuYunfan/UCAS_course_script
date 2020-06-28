import requests
import tkinter.messagebox
import tkinter
import threading
import time
from PIL import Image, ImageTk
import re


def post_data(url, data=None, time_out=3, retry=5):
    for _ in range(retry):
        try:
            page = sess.post(url, data=data, timeout=time_out)
            return page
        except:
            pass
    return None


def check_online():
    log['text'] = ''

    if select_course_payload is None:
        tkinter.messagebox.showerror(title='错误', message='您还未登录')
        return None

    page = post_data('http://jwxk.ucas.ac.cn/courseManage/selectCourse', select_course_payload)
    if page is None:
        select_result['text'] = '网页超时 没有进行选课'
        return None

    off_line = re.search('你的会话已失效或身份已改变，请重新登录', page.text)
    if off_line:
        select_result['text'] = '您已经掉线'
        login_info['text'] = '您已经掉线'
        return None

    system_closed = re.search('为了给您提供更好的服务', page.text)
    if system_closed:
        select_result['text'] = '选课系统未开放'
        return None

    select_result['text'] = '正在选课'
    return page


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
        return 1
    else:
        select_course_payload['sids'].append(course_code.group(1))
        return 0


def select_separately(event):
    select_course_page = check_online()
    if select_course_page is None:
        return

    course_list = course_input_separate.get()
    course_list = course_list.split()
    for course in course_list:
        select_course_payload['sids'] = []
        if add_course_code_to_payload(course, select_course_page):
            continue

        select_result_page = post_data('http://jwxk.ucas.ac.cn/courseManage/saveCourse', select_course_payload)
        if select_result_page is None:
            log['text'] += course + ': 网页超时'+' \n ' + sep_time['text'] + '\n'
        else:
            generate_log(select_result_page)

    select_result['text'] = '选课完成'


def select_together(event):
    select_course_page = check_online()
    if select_course_page is None:
        return

    course_list = course_input.get()
    course_list = course_list.split()
    select_course_payload['sids'] = []
    for course in course_list:
        add_course_code_to_payload(course, select_course_page)

    if len(select_course_payload['sids']) == 0:
        select_result['text'] = '课程代码均不可用'
        return

    select_result_page = post_data('http://jwxk.ucas.ac.cn/courseManage/saveCourse', select_course_payload)
    if select_result_page is None:
        select_result['text'] = '网页超时 没有进行选课'
    else:
        generate_log(select_result_page)
        select_result['text'] = '选课完成'


def login(event):
    user = user_input.get()
    pwd = pwd_input.get()
    code = cert_code_input.get()
    login_payload = {'userName': user, 'pwd': pwd, 'certCode': code, 'sb': 'sb'}

    login_info['text'] = '正在登录'
    root.update_idletasks()

    page = post_data('http://sep.ucas.ac.cn/slogin', data=login_payload)
    if page is None:
        login_info['text'] = '网页超时 请重新登录'
        return

    pattern = re.compile('&nbsp;(.+?)</li>', re.S)
    try:
        name = re.search(pattern, page.text).group(1)
    except:
        login_info['text'] = '信息有误'
        return

    page = post_data('http://sep.ucas.ac.cn/portal/site/226/821')
    if page is None:
        login_info['text'] = '网页超时 请重新登录'
        return

    pattern = re.compile('Identity=([\w-]*)')
    try:
        iden = re.search(pattern, page.text).group(1)
    except:
        login_info['text'] = '没有成功匹配到Identity，请及时联系作者'
        return

    login_info['text'] = '正在跳转'
    root.update_idletasks()

    jump_payload = {'Identity': iden}
    page = post_data('http://jwxk.ucas.ac.cn/login', data=jump_payload)
    if page is None:
        login_info['text'] = '网页超时 请重新登录'
        return

    pattern = re.compile('"_id_1">&nbsp;&nbsp;(.+?)</label>')
    try:
        student_number = re.search(pattern, page.text).group(1)
        student_number_payload = {'num': student_number, 'sb': 'y'}
        page = post_data('http://jwxk.ucas.ac.cn/doSelectNo', data=student_number_payload)
        if page is None:
            login_info['text'] = '网页超时 请重新登录'
            return
    except:
        pass

    page = post_data('http://jwxk.ucas.ac.cn/courseManage/main')
    if page is None:
        login_info['text'] = '网页超时 请重新登录'
        return
    pattern = re.compile('\?s=(.*?)";')
    select_course_s = re.search(pattern, page.text).group(1)
    pattern = re.compile('label for="id_(\d+)"')
    deptIds = re.findall(pattern, page.text)
    global select_course_payload
    select_course_payload = {'s': select_course_s, 'deptIds': deptIds, 'sb': 'y'}
    login_info['text'] = '登陆成功 ' + name


def get_time():
    while True:
        try:
            current_time = requests.get('http://jwxk.ucas.ac.cn/courseManage/main', timeout=3)
            current_time = current_time.headers
            current_time = current_time['Date']
            hour = current_time[17:19]
            minute = current_time[20:22]
            second = current_time[23:25]
            hour = int(hour) + 8
            time_str = str(hour) + ':' + minute + ':' + second
            sep_time['text'] = time_str
            time.sleep(1)
            root.update_idletasks()
        except:
            pass


def auto_select():
    global auto_working
    while True:
        if auto_working and login_info['text'] != '您已经掉线':
            select_separately(None)
        time.sleep(1)


def auto_switch(event):
    global auto_working
    if auto_working == 0:
        tkinter.messagebox.showinfo(title='提示',
                 message='1.请先使用“分开选”功能，确认提示信息为“超过限选人数”(而无其他错误)后再使用此功能\n'
                         '2.此模式每1s自动进行一次“分开选”\n'
                         '3.如若中途掉线，需要自己手动重新登录')
        jianlou_switch['text'] = '停止'
    else:
        jianlou_switch['text'] = '捡漏'
    auto_working = 1 - auto_working


def download_image_file(event):
    global sess
    sess = requests.session()
    login_info['text'] = ''
    try:
        html = sess.get('http://sep.ucas.ac.cn/changePic', timeout=3)
    except:
        login_info['text'] = '网页超时 请重新获取验证码'
        return

    fp = open("certcode.jpg", 'wb')
    fp.write(html.content)
    fp.close()
    global cert_photo
    cert_img = Image.open("certcode.jpg")
    cert_photo = ImageTk.PhotoImage(cert_img)
    show_pic['image'] = cert_photo


if __name__ == "__main__":
    auto_working = 0
    login_check = 0
    root = tkinter.Tk()
    root.title("UCAS_course_grad 1.7 by wyf && YaoBIG QQ:751076061")
    root.geometry('620x640')
    root.resizable(width=False, height=False)

    sep_time = tkinter.Label(root, font=('Calibri', '10'))
    sep_time.grid(row=0, column=1, sticky=tkinter.E)

    thread_1 = threading.Thread(target=get_time)
    thread_1.setDaemon(True)
    thread_1.start()

    thread_2 = threading.Thread(target=auto_select)
    thread_2.setDaemon(True)
    thread_2.start()

    login_info = tkinter.Label(root, text='')
    login_info.grid(row=6, column=0, sticky=tkinter.W)
    login_info['font'] = ('Calibri', '14')

    select_result = tkinter.Label(root, text='')
    select_result.grid(row=9, sticky=tkinter.W)
    select_result['font'] = ('Calibri', '14')

    tkinter.Label(root, text='用户名(同sep)', font=('Calibri', '14')).grid(row=0, column=0, sticky=tkinter.W)
    user_input = tkinter.Entry(root)
    user_input.grid(row=1, column=0, sticky=tkinter.W)
    user_input['font'] = ('Calibri', '14')
    user_input['width'] = 30

    tkinter.Label(root, text='密码', font=('Calibri', '14')).grid(row=0, column=1, sticky=tkinter.W)
    pwd_input = tkinter.Entry(root)
    pwd_input['show'] = '*'
    pwd_input['width'] = 30
    pwd_input.grid(row=1, column=1, sticky=tkinter.W)
    pwd_input['font'] = ('Calibri', '14')
    pwd_input.bind('<Key-Return>', login)

    get_pic = tkinter.Button(root, text='重新获取验证码')
    get_pic['width'] = 12
    get_pic.grid(row=5, column=1, sticky=tkinter.W)
    get_pic['font'] = ('Calibri', '14')
    get_pic.bind('<ButtonRelease-1>', download_image_file)

    show_pic = tkinter.Label(root)
    show_pic.grid(row=5, column=1, sticky=tkinter.E)
    download_image_file(None)

    tkinter.Label(root, text='验证码', font=('Calibri', '14')).grid(row=2, column=0, sticky=tkinter.W)

    cert_code_input = tkinter.Entry(root)
    cert_code_input['width'] = 30
    cert_code_input.grid(row=5, column=0, sticky=tkinter.W)
    cert_code_input['font'] = ('Calibri', '14')
    cert_code_input.bind('<Key-Return>', login)

    login_button = tkinter.Button(root, text='登 录')
    login_button['width'] = 6
    login_button['font'] = ('Calibri', '14')
    login_button.grid(row=6, column=1, sticky=tkinter.E)
    login_button.bind('<ButtonRelease-1>', login)

    tkinter.Label(root, text='课程编码（一起选） 用空格连接', font=('Calibri', '14')).grid(row=7, column=0, sticky=tkinter.W)
    course_input = tkinter.Entry(root)
    course_input['width'] = 30
    course_input.grid(row=8, column=0, sticky=tkinter.W)
    course_input['font'] = ('Calibri', '14')
    course_input.bind('<Key-Return>', select_together)

    tkinter.Label(root, text='课程编码（分开选） 用空格连接', font=('Calibri', '14')).grid(row=7, column=1, sticky=tkinter.W)
    course_input_separate = tkinter.Entry(root)
    course_input_separate['width'] = 30
    course_input_separate.grid(row=8, column=1, sticky=tkinter.W)
    course_input_separate['font'] = ('Calibri', '14')
    course_input_separate.bind('<Key-Return>', select_separately)

    course_choose = tkinter.Button(root, text='一起选')
    course_choose.bind('<ButtonRelease-1>', select_together)
    course_choose['font'] = ('Calibri', '14')
    course_choose['width'] = 6
    course_choose.grid(row=9, column=0, sticky=tkinter.E)

    course_choose = tkinter.Button(root, text='分开选')
    course_choose.bind('<ButtonRelease-1>', select_separately)
    course_choose['font'] = ('Calibri', '14')
    course_choose['width'] = 6
    course_choose.grid(row=9, column=1, sticky=tkinter.E)

    jianlou_switch = tkinter.Button(root, text='捡 漏')
    jianlou_switch.bind('<ButtonRelease-1>', auto_switch)
    jianlou_switch['font'] = ('Calibri', '14')
    jianlou_switch['width'] = 6
    jianlou_switch.grid(row=9, column=1, sticky=tkinter.W)

    tkinter.Label(root, text='Log:', font=('Calibri', '14')).grid(row=11, column=0, sticky=tkinter.W)
    log = tkinter.Label(root, anchor='nw', justify='left', background='white', relief='sunken', height=21, width=50,
                        borderwidth=2)
    log.grid(row=12, column=0, sticky=tkinter.W)
    log['font'] = ('Calibri', '9')

    tkinter.Label(root, text='Log_Success:', font=('Calibri', '14')).grid(row=11, column=1, sticky=tkinter.W)
    log_success = tkinter.Label(root, anchor='nw', justify='left', background='white', relief='sunken', height=21,
                                width=50, borderwidth=2)
    log_success.grid(row=12, column=1, sticky=tkinter.W)
    log_success['font'] = ('Calibri', '9')

    root.mainloop()

