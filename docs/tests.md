# 🧪 Documentação e Cobertura de Testes Automatizados

Este documento descreve a organização da suíte de testes automatizados do **Sistema de Reservas de Hotel**, implementada com o framework **pytest**. A suíte conta com **236 testes automatizados**, divididos em módulos especializados que cobrem desde invariantes de domínio e regras de negócio até persistência relacional e contratos HTTP.

---

## 📊 Visão Geral da Suíte

```bash
# Execução completa da suíte de testes
pytest -v
```

| Diretório de teste | Qtd. Testes | Escopo Principal |
| :--- | :---: | :--- |
| [`tests/test_models.py`](../tests/test_models.py) | **26** | Invariantes de entidades, validações com `@property`, métodos especiais e mixins. |
| [`tests/test_rates.py`](../tests/test_rates.py) | **43** | Precificação dinâmica, funções puras, temporadas, fins de semana e polimorfismo. |
| [`tests/test_rules.py`](../tests/test_rules.py) | **35** | Regras de negócio, ciclo de vida da reserva, tolerâncias, cancelamento e no-show. |
| [`tests/test_reports.py`](../tests/test_reports.py) | **62** | Precisão estatística dos indicadores gerenciais (Taxa de Ocupação, ADR e RevPAR). |
| [`tests/test_database.py`](../tests/test_database.py) | **4** | Inicialização do SQLite, integridade referencial, constraints e serialização JSON. |
| [`tests/test_api.py`](../tests/test_api.py) | **66** | Integração HTTP dos 24 endpoints FastAPI, CRUDs, schemas Pydantic e códigos de status. |
| **Total Consolidado** | **236** | **Suíte completa de validação contínua (CI/CD)** |

---

## 🔍 Principais testes

### 1. `tests/test_models.py` (26 testes)
Valida a camada de domínio puro (`src/models/`), garantindo encapsulamento rígido e contratos de orientação a objetos:
* **Validação de Hóspede e Pessoa:** Testa criação correta, rejeição de e-mail com formato inválido por regex (`DadosInvalidosException`), bloqueio de nomes/documentos vazios e cópia defensiva da lista de histórico de reservas.
* **Hierarquia e Polimorfismo de Quartos:** Valida restrições de tarifa positiva e capacidade mínima ($\ge 1$), cálculo com acréscimo de varanda em `QuartoDuplo`, cálculo com taxa de serviço em `QuartoLuxo`, e métodos operacionais de interdição e liberação de manutenção (`bloquear_manutencao` e `liberar_manutencao`).
* **Pagamentos e Adicionais:** Validação de métodos permitidos (`MetodoPagamento`), bloqueio de quantias negativas e cálculo do montante total por item (`preco_unitario * quantidade`).
* **Invariantes e Máquina de Estados em Reserva:** Validação de data de entrada anterior à de saída, barramento de quantidade de hóspedes superior à capacidade do quarto (`CapacidadeExcedidaException`), e transições de estado controladas.
* **Cronologia do Check-out:** Rejeita saída anterior ao check-in real e ausência desse registro, sem alterar reserva, quarto, auditoria ou adicionais. Aceita horário igual ou posterior ao check-in quando o pagamento está quitado.
* **Métodos Especiais (*Dunder Methods*):**
  * `Reserva.__len__`: Retorna o número exato de diárias.
  * `Reserva.__eq__`: Compara igualdade de alocação por quarto e período.
  * `Quarto.__lt__`: Ordenação natural por tipo/categoria e número.
  * `__str__` e `__repr__`: Representações amigáveis e técnicas para depuração.
* **Mixins Transversais:** Validação da herança cooperativa em `Auditoria` (registro de carimbos temporais) e `Serializavel` (`to_dict`, `to_json`, `from_dict`).

---

### 2. `tests/test_rates.py` (43 testes)
Testa o serviço `CalculadoraTarifa` (`src/services/rates.py`) como conjunto de funções puras e determinísticas:
* **Dias Úteis vs. Finais de Semana:** Garante tarifa integral sem alteração em dias úteis e aplicação correta dos multiplicadores de sexta-feira, sábado e domingo.
* **Limites e Intervalos de Temporadas:** Verifica que as datas de início e fim da temporada são inclusivas, e que diárias fora do período voltam ao preço base.
* **Cumulação de Políticas:** Valida a combinação multiplicativa de temporada e fim de semana.
* **Cálculo da Estadia Completa:** Testa a soma acumulada dia a dia em reservas que atravessam transições de mês, temporadas e fins de semana, excluindo a data de saída.
* **Robustez de Dados:** Rejeita multiplicadores nulos, booleanos, infinitos ou negativos com `DadosInvalidosException`.

---

### 3. `tests/test_rules.py` (35 testes)
Valida a lógica operacional do serviço `Hotel` (`src/services/hotel.py`) utilizando banco SQLite temporário isolado por teste:
* **Prevenção de Overbooking:** Testa sobreposições parciais, totais e contidas de datas para o mesmo quarto, disparando `QuartoIndisponivelException` e aceitando estadias consecutivas onde a saída coincide com a nova entrada.
* **Controle de Manutenção:** Garante que quartos em manutenção não apareçam em buscas de disponibilidade e barrem novas reservas.
* **Check-in e Tolerâncias:** Validação da janela de horário (a partir das 14:00 com tolerância configurável de 30 minutos), rejeitando entradas antes do horário mínimo permitido.
* **Check-out e Quitação Financeira:** Exigência de quitação total (`total_pago >= total_devido`), disparando `PagamentoInsuficienteException` em caso de saldo devedor e cobrando diária extra por atrasos após as 12:30.
* **Cancelamento com Multa:** Aplicação da política configurada no `settings.json` (multa de 50% para cancelamentos com menos de 48h de antecedência e cancelamento gratuito $\ge 48\text{h}$).
* **Varredura de No-Show:** Identificação de reservas confirmadas cujo hóspede não compareceu após a tolerância de 120 minutos, alterando status para `NO_SHOW` e liberando o quarto.

---

### 4. `tests/test_reports.py` (62 testes)
Testa exaustivamente o motor de indicadores do `ServicoRelatorios` (`src/services/reports.py`):
* **Taxa de Ocupação (%):** Valida inventário vazio (0.0%), ocupação parcial e total, recorte rigoroso de estadias que cruzam as fronteiras do período, exclusão do dia da saída e desconsideração de reservas canceladas ou em `NO_SHOW`.
* **ADR (*Average Daily Rate*):** Valida a média de receita de hospedagem por noite vendida em estadias finalizadas (`CHECKOUT`), garantindo o rateio proporcional em estadias parciais e a exclusão de itens de consumo adicional.
* **RevPAR (*Revenue per Available Room*):** Valida a receita por quarto disponível dividida pelo total de quartos cadastrados no inventário multiplicados pelos dias do período, incluindo quartos não vendidos.
* **Imutabilidade e Robustez:** Assegura que a extração de relatórios não modifica o estado interno de quartos ou reservas e rejeita períodos com `inicio >= fim`.

---

### 5. `tests/test_database.py` (4 testes)
Valida a camada de infraestrutura e persistência relacional (`src/database/`):
* **Inicialização de Tabelas e Constraints:** Garante a criação de tabelas (`quartos`, `hospedes`, `temporadas`, `reservas`) com chaves estrangeiras ativas (`PRAGMA foreign_keys = ON`).
* **CRUD e Integridade Relacional:** Testa inserção, consulta e atualização de registros de quartos, hóspedes e reservas.
* **Serialização e Desserialização JSON:** Valida a persistência das listas relacionais de `pagamentos` e `adicionais` em formato JSON dentro do registro relacional da reserva.

---

### 6. `tests/test_api.py` (66 testes)
Testa os contratos de interface REST expostos pela API FastAPI (`src/api/routes.py`):
* **CRUDs de Quartos e Hóspedes:** Criação, listagem, consulta individual, atualização e exclusão persistidas no SQLite. Verifica exclusão com resposta `204` sem corpo, identificadores inexistentes (`404`) e documento duplicado (`409`).
* **Preservação de Vínculos:** Impede exclusão de cadastros com reservas e redução de capacidade que inviabilize reservas existentes, incluindo históricas. Edições preservam o estado do quarto, os dados de manutenção e os valores de diárias já contratados.
* **Atualizações Inválidas:** Garante que dados cadastrais inválidos sejam recusados sem alterar os dados persistidos.
* **Check-out Anterior ao Check-in:** Retorna `400` tanto para dia anterior quanto para horário anterior no mesmo dia, preserva a estadia e os valores salvos e permite uma nova tentativa com data correta.
* **Ciclo de Atendimento Completo (`test_fluxo_completo_de_atendimento`):** Executa o fluxo de ponta a ponta: cadastro de quarto e hóspede $\rightarrow$ bloqueio/desbloqueio $\rightarrow$ criação de reserva $\rightarrow$ check-in $\rightarrow$ adicionais $\rightarrow$ pagamento $\rightarrow$ check-out $\rightarrow$ relatórios (Ocupação, ADR, RevPAR e Financeiro) $\rightarrow$ cancelamento com multa e varredura de no-show.
* **Validação de Schemas Pydantic (HTTP 422):** Testa rejeição de dados obrigatórios ausentes, tipos incompatíveis e valores inválidos (ex.: capacidade zero, método de pagamento inexistente).
* **Tratamento Semântico de Erros:**
  * `400 Bad Request`: Datas inconsistentes, capacidade excedida ou check-in antecipado.
  * `402 Payment Required`: Check-out com pendência de saldo devedor.
  * `404 Not Found`: IDs inexistentes de reservas, quartos ou hóspedes.
  * `409 Conflict`: Tentativa de cadastrar quartos com numeração duplicada ou hóspedes com mesmo documento.
* **Validação dos Endpoints de Relatórios:** Garante que `/relatorios/ocupacao`, `/relatorios/adr`, `/relatorios/revpar` e `/relatorios/financeiro` rejeitem intervalos inconsistentes com status 400.

