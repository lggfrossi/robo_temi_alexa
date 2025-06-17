# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.

import logging
import os
import requests
import ask_sdk_core.utils as ask_utils

from ask_sdk_s3.adapter import S3Adapter
from ask_sdk_core.utils import get_slot_value
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "O que deseja fazer? Ver o robô listado, os pontos de movimentação do robô no mapa, criar uma missão de fala ou uma missão de movimentação?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class GetRobotsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetRobotsIntent")(handler_input)

    def handle(self, handler_input):
        app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
        api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"
        
        url = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/robots"
        headers = {
            "x-api-key": api_key
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if "robots" in data and isinstance(data["robots"], list) and len(data["robots"]) > 0:
                mensagens = []
                for robot in data["robots"]:
                    nome = robot.get("name", "sem nome")
                    codigo = robot.get("code", "sem código")
                    tipo = robot.get("type", "desconhecido")
                    status = robot.get("status", "sem status")

                    mensagem = f"O robô disponível é o {nome}. Ele é do tipo {tipo}, tem o código {codigo} e está atualmente {status}."
                    mensagens.append(mensagem)

                speak_output = " ".join(mensagens)
            else:
                speak_output = "Não encontrei robôs disponíveis."

        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
            speak_output = "Ocorreu um erro ao buscar os robôs. Tente novamente mais tarde."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Deseja fazer outra consulta?")
                .response
        )


class GetMapPointsIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("GetMapPointsIntent")(handler_input)

    def handle(self, handler_input):
        app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
        api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"

        url = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/settings/map"
        headers = {
            "x-api-key": api_key
        }
        params = {
            "robot_type": "temi"
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()

            if "map" in data and "points" in data["map"]:
                pontos = data["map"]["points"]

                if pontos:
                    nomes = [p.get("name", "sem nome") for p in pontos]

                    if len(nomes) == 1:
                        pontos_texto = nomes[0]
                    elif len(nomes) == 2:
                        pontos_texto = " e ".join(nomes)
                    else:
                        pontos_texto = ", ".join(nomes[:-1]) + " e " + nomes[-1]

                    speak_output = f"Os pontos de movimentação no mapa registrados são: {pontos_texto}."
                else:
                    speak_output = "Não há pontos de movimentação registrados no mapa."
            else:
                speak_output = "Não consegui encontrar o mapa ou os pontos registrados."

        except Exception as e:
            logger.error(f"Erro ao buscar pontos do mapa: {e}")
            speak_output = "Ocorreu um erro ao buscar os pontos do mapa. Tente novamente mais tarde."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask("Deseja saber mais alguma coisa?")
                .response
        )



class CriarMissaoFalaIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CriarMissaoFalaIntent")(handler_input)

    def handle(self, handler_input):
        mensagem = ask_utils.get_slot_value(handler_input, "mensagem_texto")

        app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
        api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"
        robot_id = "lzmohkxuB_A12jikg8jZoGINlqwJf"
        url = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/conversation/message"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        body = {
            "robot_type": "temi",
            "target_robot": robot_id,
            "expiration": 300,
            "message": {
                "text": mensagem,
                "language": "pt_BR"
            }
        }

        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            if response.status_code == 200:
                resposta = response.json()
                mission_id = resposta.get("mission_id", "desconhecida")
                nome = resposta.get("robot", {}).get("name", "desconhecido")
                expires = resposta.get("expires_at", "tempo desconhecido")

                # Salva mission_id nos atributos persistentes
                attributes_manager = handler_input.attributes_manager
                persistent_attrs = attributes_manager.persistent_attributes or {}
                persistent_attrs["mission_id"] = mission_id
                attributes_manager.persistent_attributes = persistent_attrs
                attributes_manager.save_persistent_attributes()

                logger.info(f"[CriarMissaoFalaIntent] Missão salva com ID: {mission_id}")
                speak_output = f"Mensagem enviada com sucesso! O robô vai falar a mensagem que você escolheu. Agora, você pode ver a missão, acompanhando o status dela ou cancelar ela, o que deseja?"
            else:
                speak_output = f"Erro ao criar missão. Código: {response.status_code}"

        except Exception as e:
            logger.error(f"Erro na missão com mensagem: {e}")
            speak_output = "Ocorreu um erro ao criar a missão. Tente novamente."

        return handler_input.response_builder.speak(speak_output).ask("Deseja fazer mais alguma coisa?").response


class VerMissaoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("VerMissaoIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("Iniciando VerMissaoIntentHandler...")

        app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
        api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"

        try:
            attributes_manager = handler_input.attributes_manager

            # Use o atributo direto
            persistent_attrs = attributes_manager.persistent_attributes
            logger.info(f"[VerMissaoIntent] Atributos carregados: {persistent_attrs}")

            mission_id = persistent_attrs.get("mission_id")
            if not mission_id:
                return handler_input.response_builder.speak("Não há missão registrada.").response

            url = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/missions/{mission_id}"
            headers = {"x-api-key": api_key}
            response = requests.get(url, headers=headers, timeout=10)

            logger.info(f"[VerMissaoIntent] Status da API: {response.status_code}, Resposta: {response.text}")

            if response.status_code == 200:
                mission = response.json()
                status = mission.get("status", "desconhecido")
                tipo = mission.get("type", "tipo indefinido")
                speak_output = f"A missão atual está com status: {status}. O robô já está executando a missão ou está se preparando para realizá-la."
            elif response.status_code == 404:
                speak_output = f"Você ainda não criou nenhuma missão ativa. Deseja criar alguma missão de fala ou uma missão de movimentação?"
            else:
                speak_output = f"Erro ao recuperar a missão. Código {response.status_code}."

        except Exception as e:
            logger.error(f"[VerMissaoIntent] Erro ao consultar missão: {e}")
            speak_output = "Ocorreu um erro ao consultar a missão, pergunte ou peça novamente."

        return handler_input.response_builder.speak(speak_output).ask("Deseja saber mais alguma coisa?").response


class CriarMissaoMovimentacaoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CriarMissaoMovimentacaoIntent")(handler_input)

    def handle(self, handler_input):
        from ask_sdk_model.dialog import DelegateDirective
        logger.info("Iniciando CriarMissaoMovimentacaoIntentHandler...")

        intent = handler_input.request_envelope.request.intent

        # Se o slot ainda não foi preenchido, buscar os pontos para informar o usuário
        if handler_input.request_envelope.request.dialog_state.value != "COMPLETED":
            app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
            api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"
            url = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/settings/map"
            headers = {"x-api-key": api_key}
            try:
                response = requests.get(url, headers=headers, params={"robot_type": "temi"}, timeout=10)
                pontos = response.json()["map"]["points"]
                nomes = [p["name"] for p in pontos]
                lista_pontos = ", ".join(nomes)
                reprompt_text = f"Para onde deseja enviar o robô? Os locais disponíveis são: {lista_pontos}."
            except Exception as e:
                logger.error(f"[CriarMissaoMovimentacaoIntent] Erro ao buscar pontos: {e}")
                reprompt_text = "Para onde deseja enviar o robô?"

            return handler_input.response_builder.speak(reprompt_text).ask(reprompt_text).add_directive(DelegateDirective(updated_intent=intent)).response

        # Slot preenchido: seguir com a criação da missão
        ponto_nome = ask_utils.get_slot_value(handler_input, "ponto_destino")

        app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
        api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"
        robot_id = "lzmohkxuB_A12jikg8jZoGINlqwJf"
        url_pontos = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/settings/map"
        url_missao = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/conversation/navigation"

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(url_pontos, headers=headers, params={"robot_type": "temi"}, timeout=10)
            pontos = response.json()["map"]["points"]

            normalizacao = {
                "1": "consultorio1", "um": "consultorio1", "uma": "consultorio1",
                "2": "consultorio2", "dois": "consultorio2", "duas": "consultorio2",
                "3": "consultorio3", "tres": "consultorio3", "três": "consultorio3",
                "consultorio 1": "consultorio1", "consultório 1": "consultorio1",
                "consultorio 2": "consultorio2", "consultório 2": "consultorio2",
                "consultorio 3": "consultorio3", "consultório 3": "consultorio3",
            }

            nome_normalizado = normalizacao.get(
                ponto_nome.strip().lower(),
                ponto_nome.strip().replace(" ", "").lower()
            )

            ponto = next((p for p in pontos if p["name"].lower() == nome_normalizado), None)

            if not ponto:
                return handler_input.response_builder.speak(
                    f"O ponto {ponto_nome} não foi encontrado no mapa."
                ).ask(
                    "Deseja tentar outro ponto?"
                ).response

            body = {
                "robot_type": "temi",
                "target_robot": robot_id,
                "expiration": 300,
                "point": {
                    "id": ponto["id"],
                    "name": ponto["name"],
                    "reference": ponto["reference"]
                },
                "on_started": {
                    "language": "pt_BR",
                    "text": "Estou iniciando a movimentação."
                },
                "on_finished": {
                    "language": "pt_BR",
                    "text": "Cheguei ao destino."
                }
            }

            response = requests.post(url_missao, headers=headers, json=body, timeout=10)

            if response.status_code == 200:
                data = response.json()
                mission_id = data.get("mission_id", "desconhecida")
                expires = data.get("expires_at", "tempo desconhecido")

                attributes_manager = handler_input.attributes_manager
                persistent_attrs = attributes_manager.persistent_attributes
                persistent_attrs["mission_id"] = mission_id
                attributes_manager.save_persistent_attributes()

                speak_output = f"Tudo certo! O robô está a caminho do {ponto_nome}. Se quiser, pode me pedir para ver a missão ou cancelar ela. O que deseja?"
            else:
                speak_output = f"Erro ao criar missão. Código de erro: {response.status_code}."

        except Exception as e:
            logger.error(f"[CriarMissaoMovimentacaoIntent] Erro: {e}")
            speak_output = "Houve um erro ao criar a missão de movimentação. Tente novamente mais tarde."

        return handler_input.response_builder.speak(speak_output).ask("Deseja fazer mais alguma coisa?").response



class CancelarMissaoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("CancelarMissaoIntent")(handler_input)

    def handle(self, handler_input):
        logger.info("Iniciando CancelarMissaoIntentHandler...")

        app_id = "m60zzrlxyyPNLnw1Hkjov9qVVdVW4"
        api_key = "fcdc801d852b8c3f49258e363081f595a9e3336b10969e9e8b1d39a6e17d30ce"

        try:
            attributes_manager = handler_input.attributes_manager
            persistent_attrs = attributes_manager.persistent_attributes
            mission_id = persistent_attrs.get("mission_id")

            if not mission_id:
                return handler_input.response_builder.speak("Não há missão ativa para cancelar.").ask("Deseja fazer outra coisa?").response

            url = f"https://api.robots.pluginbot.ai/app-integration/v1/apps/{app_id}/missions/{mission_id}"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "text/plain;charset=UTF-8"
            }

            response = requests.delete(url, headers=headers, timeout=10)

            if response.status_code == 200:
                status = response.json().get("status", "desconhecido")
                # Opcionalmente limpa o mission_id
                persistent_attrs["mission_id"] = None
                attributes_manager.persistent_attributes = persistent_attrs
                attributes_manager.save_persistent_attributes()
                speak_output = f"A missão foi cancelada com sucesso. O robô pode receber novas missões, seja de fala ou movimentação."
            else:
                speak_output = f"Não foi possível cancelar a missão. Código de erro: {response.status_code}."

        except Exception as e:
            logger.error(f"[CancelarMissaoIntent] Erro: {e}")
            speak_output = "Ocorreu um erro ao tentar cancelar a missão. Tente novamente mais tarde."

        return handler_input.response_builder.speak(speak_output).ask("Deseja fazer mais alguma coisa?").response


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Desculpe, não entendi. Você pode tentar dizer, por exemplo: abrir robo temi"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Desculpe, tive um problema para realizar esse comando. Quer tentar novamente?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


s3_adapter = S3Adapter(bucket_name="alexa-temi-armazenamento")
sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GetRobotsIntentHandler())
sb.add_request_handler(GetMapPointsIntentHandler())
sb.add_request_handler(CriarMissaoFalaIntentHandler())
sb.add_request_handler(VerMissaoIntentHandler())
sb.add_request_handler(CriarMissaoMovimentacaoIntentHandler())
sb.add_request_handler(CancelarMissaoIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()