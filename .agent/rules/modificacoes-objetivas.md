---
trigger: always_on
---

Regra: Modificação mínima ao corrigir bugs

Contexto: Esta regra se aplica somente quando o agente estiver corrigindo bugs em funcionalidades já existentes.
Para criação de código novo (novos arquivos, novas funções, novas features), o agente tem liberdade total.

🛠 Correção de bugs em código existente

Quando a instrução do usuário for corrigir um bug em uma funcionalidade que já existe, o agente deve:

✅ Modificar o mínimo possível de código

Priorizar ajustes pontuais em vez de reescrever blocos grandes.

Evitar refatorações amplas, mudanças de estilo ou “melhorias” não solicitadas.

Manter a estrutura geral do arquivo e dos métodos inalterada, a menos que seja estritamente necessário para corrigir o bug.

✅ Preservar a lógica que já está funcionando

Não alterar comportamentos que não estejam relacionados diretamente ao bug descrito.

Não mudar assinaturas de funções (nome, parâmetros, retorno) se isso não for essencial para a correção.

Não mudar contratos de APIs, interfaces ou DTOs, exceto se o bug for diretamente sobre isso.

✅ Ser explícito sobre o que foi alterado

Comentar brevemente (em linguagem natural) no chat quais linhas ou trechos foram modificados e o motivo.

Se possível, indicar:

Onde estava o problema.

Qual foi a correção mínima aplicada.

🚫 O que evitar ao corrigir bugs

Não reescrever funções inteiras quando só um detalhe interno precisa ser ajustado.

Não mover código entre arquivos sem necessidade.

Não introduzir novos padrões, frameworks ou bibliotecas durante uma simples correção de bug.

🆕 Criação de código ou arquivos novos

Quando a instrução do usuário for criar novas funcionalidades, novos arquivos ou novos módulos, o agente:

🟢 Tem liberdade total para:

Criar quantas funções, classes e linhas de código forem necessárias.

Definir a estrutura, organização e padrões internos do novo código.

Refatorar apenas o que for estritamente necessário para integrar a nova funcionalidade ao código existente.