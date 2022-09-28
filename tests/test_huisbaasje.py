from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop, TestServer
from aiohttp.web_request import Request

from huisbaasje import Huisbaasje


class HuisbaasjeTestCase(AioHTTPTestCase):
    async def get_application(self):
        async def authenticate(request: Request):
            data = await request.post()
            assert data["username"] == "username"
            assert data["password"] == "password"
            assert data["grant_type"] == "password"
            assert data["client_id"] == "b58efc0b"
            assert data["scope"] == "role:enduser realm:aurum"
            with open("tests/responses/authentication.json") as file:
                return web.Response(
                    content_type="application/json",
                    text=file.read()
                )

        async def customer_overview(request: Request):
            assert request.headers["Authorization"] == "Bearer acc35500-abcd-abcd-abcd-1234567890ab"
            with open("tests/responses/customer_overview.json") as file:
                return web.Response(
                    content_type="application/json",
                    text=file.read()
                )

        async def actuals(request: Request):
            assert request.headers["Authorization"] == "Bearer acc35500-abcd-abcd-abcd-1234567890ab"
            assert request.query["sources"] == "00000000-0000-0000-0000-000000000005," \
                                               "00000000-0000-0000-0000-000000000001," \
                                               "00000000-0000-0000-0000-000000000002," \
                                               "00000000-0000-0000-0000-000000000003," \
                                               "00000000-0000-0000-0000-000000000004," \
                                               "00000000-0000-0000-0000-000000000006," \
                                               "00000000-0000-0000-0000-000000000007," \
                                               "00000000-0000-0000-0000-000000000008," \
                                               "00000000-0000-0000-0000-000000000009," \
                                               "00000000-0000-0000-0000-000000000010"
            with open("tests/responses/actuals.json") as file:
                return web.Response(
                    content_type="application/json",
                    text=file.read()
                )

        app = web.Application()
        app.router.add_post('/oauth2/v1/token', authenticate)
        app.router.add_get('/user/v3/customers/overview', customer_overview)
        app.router.add_get('/user/v3/customers/12345678-abcd-abcd-abcd-1234567890ab/actuals', actuals)
        return app

    @unittest_run_loop
    async def test_authenticate_success(self):
        huisbaasje = Huisbaasje(
            "username",
            "password",
            api_scheme="http",
            api_host="localhost",
            api_port=self.server.port
        )
        await huisbaasje.authenticate()

        assert huisbaasje.is_authenticated()
        assert huisbaasje._auth_token == "acc35500-abcd-abcd-abcd-1234567890ab"

    @unittest_run_loop
    async def test_customer_overview(self):
        huisbaasje = Huisbaasje(
            "username",
            "password",
            api_scheme="http",
            api_host="localhost",
            api_port=self.server.port
        )
        await huisbaasje.authenticate()
        await huisbaasje.customer_overview()

        assert huisbaasje.get_user_id() == "12345678-abcd-abcd-abcd-1234567890ab"
        assert huisbaasje.get_source_ids() == [
            "00000000-0000-0000-0000-000000000005",
            "00000000-0000-0000-0000-000000000001",
            "00000000-0000-0000-0000-000000000002",
            "00000000-0000-0000-0000-000000000003",
            "00000000-0000-0000-0000-000000000004",
            "00000000-0000-0000-0000-000000000006",
            "00000000-0000-0000-0000-000000000007",
            "00000000-0000-0000-0000-000000000008",
            "00000000-0000-0000-0000-000000000009",
            "00000000-0000-0000-0000-000000000010"
            # Source ids only contain ids of supported types,
            # so sources "00000000-0000-0000-0000-000000000011" and "00000000-0000-0000-0000-000000000012"
            # are not in this list
        ]

    @unittest_run_loop
    async def test_actuals(self):
        huisbaasje = Huisbaasje(
            "username",
            "password",
            api_scheme="http",
            api_host="localhost",
            api_port=self.server.port
        )
        await huisbaasje.authenticate()
        await huisbaasje.customer_overview()
        actuals = await huisbaasje.actuals()

        assert len(actuals) == 10
        assert "electricity" in actuals
        assert "electricityIn" in actuals
        assert "electricityInLow" in actuals
        assert "electricityOut" in actuals
        assert "electricityOutLow" in actuals
        assert "electricityExpected" in actuals
        assert "electricityGoal" in actuals
        assert "gas" in actuals
        assert "gasExpected" in actuals
        assert "gasGoal" in actuals
        assert actuals["electricity"]["type"] == "electricity"
        assert actuals["electricity"]["source"] == "sourceId5"
        assert len(actuals["electricity"]["measurements"]) == 29
        assert actuals["electricity"]["thisDay"]["value"] == 1.7883327720000002
        assert actuals["electricity"]["thisWeek"]["value"] == 3.931665413

    @unittest_run_loop
    async def test_current_measurements(self):
        huisbaasje = Huisbaasje(
            "username",
            "password",
            api_scheme="http",
            api_host="localhost",
            api_port=self.server.port
        )
        current_measurements = await huisbaasje.current_measurements()

        assert len(current_measurements) == 10
        assert "electricity" in current_measurements
        assert "electricityIn" in current_measurements
        assert "electricityInLow" in current_measurements
        assert "electricityOut" in current_measurements
        assert "electricityOutLow" in current_measurements
        assert "electricityExpected" in current_measurements
        assert "electricityGoal" in current_measurements
        assert "gas" in current_measurements
        assert "gasExpected" in current_measurements
        assert "gasGoal" in current_measurements
        assert current_measurements["electricity"]["measurement"]["rate"] == 246.66666666666669
        assert current_measurements["electricity"]["measurement"]["time"] == "2020-06-14T11:08:20.000Z"
        assert current_measurements["electricity"]["thisDay"]["value"] == 1.7883327720000002
        assert current_measurements["electricity"]["thisDay"]["cost"] == 0.35766655440000006
        assert current_measurements["electricity"]["thisWeek"]["value"] == 3.931665413
        assert current_measurements["electricity"]["thisWeek"]["cost"] == 0.7863330826000001
