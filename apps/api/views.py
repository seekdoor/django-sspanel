import uuid
from typing import List

import pendulum
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ext import lock
from apps.proxy import models as m
from apps.sspanel import tasks
from apps.sspanel.models import Goods, User, UserCheckInLog, UserOrder
from apps.sub import UserSubManager
from apps.tianyi import DashBoardManger
from apps.utils import (
    api_authorized,
    gen_datetime_list,
    get_client_ip,
    get_current_datetime,
    handle_json_request,
    is_ip_address,
    traffic_format,
)


class SystemStatusView(View):
    @method_decorator(permission_required("sspanel"))
    def get(self, request):
        start = pendulum.parse(request.GET["start"])
        end = pendulum.parse(request.GET["end"])
        dt_list = [start.add(days=i) for i in range((end - start).days + 1)]
        dm = DashBoardManger(dt_list)
        data = {
            "node_status": dm.get_node_status(),
            "user_status": dm.get_user_status_data(),
            "order_status": dm.get_userorder_status_data(),
        }
        return JsonResponse(data)


class UserSettingsView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UserSettingsView, self).dispatch(*args, **kwargs)

    @method_decorator(login_required)
    def post(self, request):
        if request.user.update_proxy_config_from_dict(data=dict(request.POST.items())):
            data = {
                "title": "修改成功!",
                "status": "success",
                "subtitle": "请及时更换客户端配置!",
            }
        else:
            data = {
                "title": "修改失败!",
                "status": "error",
                "subtitle": "配置更新失败请重试!可能是密码太简单了",
            }
        return JsonResponse(data)


class UserNodeBaseView(View):
    def get_user_and_nodes(self, request):
        if uid := request.GET.get("uid"):
            try:
                uuid.UUID(uid)
            except ValueError:
                return None, HttpResponseBadRequest("invalid uid")
        else:
            return None, HttpResponseBadRequest("uid is required")

        user = User.objects.filter(uid=uid).first()
        if not user:
            return None, HttpResponseBadRequest("user not found")

        node_list = m.ProxyNode.get_user_active_nodes(user)
        native_ip = request.GET.get("native_ip")
        if native_ip:
            node_list = node_list.filter(native_ip=True)
        location = request.GET.get("location")
        if location:
            node_list = node_list.filter(country=location)

        if node_list.count() == 0:
            return user, [m.ProxyNode.fake_node("当前没有可用节点")]
        return user, node_list


class SubscribeView(UserNodeBaseView):
    def get(self, request):
        user, response_or_nodes = self.get_user_and_nodes(request)
        if not isinstance(response_or_nodes, HttpResponse):
            node_list = response_or_nodes

            if protocol := request.GET.get("protocol"):
                if (
                    protocol in m.ProxyNode.NODE_TYPE_SET
                    and type(node_list) is QuerySet
                ):
                    node_list = node_list.filter(node_type=protocol)

            sub_client = request.GET.get("client")
            if not sub_client:
                ua = request.META["HTTP_USER_AGENT"].lower()
                if "clash" in ua:
                    sub_client = UserSubManager.CLIENT_CLASH
                else:
                    sub_client = UserSubManager.CLIENT_SHADOWROCKET
            try:
                sub_info = UserSubManager(user, node_list, sub_client).get_sub_info()
            except ValueError as e:
                return HttpResponseBadRequest(str(e))
            return HttpResponse(
                sub_info,
                content_type="text/plain; charset=utf-8",
                headers=user.get_sub_info_header(
                    for_android=sub_client != UserSubManager.CLIENT_SHADOWROCKET
                ),
            )
        else:
            return response_or_nodes


class ClashProxyProviderView(UserNodeBaseView):
    def get(self, request):
        user, response_or_nodes = self.get_user_and_nodes(request)
        if not isinstance(response_or_nodes, HttpResponse):
            node_list = response_or_nodes
            providers = UserSubManager(user, node_list).get_clash_proxy_providers()
            return HttpResponse(
                providers,
                content_type="text/plain; charset=utf-8",
            )
        else:
            return response_or_nodes


class ClashDirectRuleSetBaseView(UserNodeBaseView):
    def get_rule_set(self, node_list, is_ip: bool):
        rule_set = set()
        for node in node_list:
            if node.enable_relay:
                for rule in node.get_enabled_relay_rules():
                    if is_ip == is_ip_address(rule.relay_host):
                        rule_set.add(rule.relay_host)
            if node.enable_direct:
                if is_ip == is_ip_address(node.server):
                    rule_set.add(node.server)
        return sorted(rule_set)


class ClashDirectDomainRuleSetView(ClashDirectRuleSetBaseView):
    def get(self, request):
        _, response_or_nodes = self.get_user_and_nodes(request)
        if not isinstance(response_or_nodes, HttpResponse):
            node_list = response_or_nodes
            domain_list = self.get_rule_set(node_list, is_ip=False)
            context = {"domain_list": domain_list}
            return render(
                request,
                "clash/direct_domain.yaml",
                context=context,
                content_type="text/plain; charset=utf-8",
            )
        else:
            return response_or_nodes


class ClashDirectIPRuleSetView(ClashDirectRuleSetBaseView):
    def get(self, request):
        _, response_or_nodes = self.get_user_and_nodes(request)
        if not isinstance(response_or_nodes, HttpResponse):
            node_list = response_or_nodes
            ip_list = self.get_rule_set(node_list, is_ip=True)
            context = {"ip_list": ip_list}
            return render(
                request,
                "clash/direct_ip.yaml",
                context=context,
                content_type="text/plain; charset=utf-8",
            )
        else:
            return response_or_nodes


class UserRefChartView(View):
    @method_decorator(login_required)
    def get(self, request):
        date = request.GET.get("date")
        t = pendulum.parse(date) if date else get_current_datetime()
        bar_configs = DashBoardManger.gen_ref_log_bar_chart_configs(
            request.user.id, [dt.date() for dt in gen_datetime_list(t)]
        )
        return JsonResponse(bar_configs)


class UserTrafficChartView(View):
    @method_decorator(login_required)
    def get(self, request):
        node_id = request.GET.get("node_id", 0)
        user_id = request.user.pk
        configs = DashBoardManger.gen_traffic_line_chart_configs(
            user_id, node_id, gen_datetime_list(get_current_datetime())
        )
        return JsonResponse(configs)


class ProxyConfigsView(View):
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(ProxyConfigsView, self).dispatch(*args, **kwargs)

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node = m.ProxyNode.get_or_none(node_id)
        return (
            JsonResponse(node.get_proxy_configs()) if node else HttpResponseBadRequest()
        )

    @method_decorator(handle_json_request)
    @method_decorator(api_authorized)
    def post(self, request, node_id):
        node = m.ProxyNode.get_or_none(node_id)
        if not node:
            return HttpResponseBadRequest()
        tasks.sync_user_traffic_task.delay(node_id, request.json)
        return JsonResponse(data={})


class EhcoRelayConfigView(View):
    """中转机器"""

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(EhcoRelayConfigView, self).dispatch(*args, **kwargs)

    @method_decorator(api_authorized)
    def get(self, request, node_id):
        node: m.RelayNode = m.RelayNode.get_or_none(node_id)
        return JsonResponse(node.get_config()) if node else HttpResponseBadRequest()

    @method_decorator(handle_json_request)
    @method_decorator(api_authorized)
    def post(self, request, node_id):
        node: m.RelayNode = m.RelayNode.get_or_none(node_id)
        if not node:
            return HttpResponseBadRequest()
        if not request.json:
            return JsonResponse(data={})

        # TODO make this async
        rules: List[m.RelayRule] = node.relay_rules.all()
        name_rule_map = {rule.name: rule for rule in rules}
        for data in request.json.get("stats", []):
            name = data["relay_label"]
            if name in name_rule_map:
                rule = name_rule_map[name]
                rule.up_traffic += data["up_bytes"] * node.enlarge_scale
                rule.down_traffic += data["down_bytes"] * node.enlarge_scale
        for rule in rules:
            rule.save()
        return JsonResponse(data={})


class UserCheckInView(View):
    @method_decorator(login_required)
    def post(self, request):
        user = request.user
        with lock.user_checkin_lock(user.pk):
            if not user.today_is_checkin:
                log = UserCheckInLog.checkin(user)
                data = {
                    "title": "签到成功！",
                    "subtitle": f"获得{traffic_format(log.increased_traffic)}流量！",
                    "status": "success",
                }
            else:
                data = {
                    "title": "签到失败！",
                    "subtitle": "今天已经签到过了",
                    "status": "error",
                }
        return JsonResponse(data)


class OrderView(View):
    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        order = UserOrder.get_and_check_recent_created_order(user)
        if order and order.status != UserOrder.STATUS_CREATED:
            info = {
                "title": "充值成功!",
                "subtitle": "请去商品界面购买商品！",
                "status": "success",
            }
        else:
            info = {
                "title": "支付查询失败!",
                "subtitle": "亲，确认支付了么？",
                "status": "error",
            }
        return JsonResponse({"info": info})

    @method_decorator(login_required)
    def post(self, request):
        try:
            amount = int(request.POST.get("num"))
            if amount < 1 or amount > 1000:
                raise ValueError
        except ValueError:
            return JsonResponse(
                {
                    "info": {
                        "title": "校验失败",
                        "subtitle": "请保证金额正确",
                        "status": "error",
                    }
                },
            )

        if settings.CHECK_PAY_REQ_IP_FROM_CN:
            from ipicn import is_in_china

            if not is_in_china(get_client_ip(request)):
                return JsonResponse(
                    {
                        "info": {
                            "title": "校验失败",
                            "subtitle": "支付时请不要使用代理软件",
                            "status": "error",
                        }
                    }
                )

        order = UserOrder.get_or_create_order(request.user, amount)
        info = {
            "title": "请求成功！",
            "subtitle": "支付宝扫描下方二维码付款，付款完成记得按确认哟！",
            "status": "success",
        }
        return JsonResponse(
            {"info": info, "qrcode_url": order.qrcode_url, "order_id": order.id}
        )


@login_required
@require_http_methods(["POST"])
def purchase(request):
    good_id = request.POST.get("goodId")
    good = Goods.objects.get(id=good_id)
    return (
        JsonResponse(
            {
                "title": "购买成功",
                "status": "success",
                "subtitle": "重新订阅即可获取所有节点",
            }
        )
        if good.purchase_by_user(request.user)
        else JsonResponse(
            {"title": "余额不足", "status": "error", "subtitle": "先去捐赠充值那充值"}
        )
    )


@login_required
def change_theme(request):
    """
    更换用户主题
    """
    theme = request.POST.get("theme", "default")
    user = request.user
    user.theme = theme
    user.save()
    res = {
        "title": "修改成功！",
        "subtitle": "主题更换成功，刷新页面可见",
        "status": "success",
    }
    return JsonResponse(res)


@login_required
def reset_sub_uid(request):
    """
    更换用户订阅 uid
    """
    user = request.user
    user.reset_sub_uid()
    res = {
        "title": "修改成功！",
        "subtitle": "订阅更换成功，刷新页面可见",
        "status": "success",
    }
    return JsonResponse(res)


@csrf_exempt
@require_http_methods(["POST"])
def ailpay_callback(request):
    data = request.POST.dict()
    if UserOrder.handle_callback_by_alipay(data):
        return HttpResponse("success")
    else:
        return HttpResponse("failure")
